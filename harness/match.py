"""Match runner for chess games between UCI engines.

Orchestrates head-to-head matches between two engine specifications under
strict time controls and opening books.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time

import chess
import chess.engine
import chess.pgn

from harness.openings import OPENINGS
from harness.versions import EngineSpec


@dataclass
class TimeControl:
    base_s: float
    inc_s: float

    @classmethod
    def parse(cls, text: str) -> "TimeControl":
        """Parse time control from string like '10+0.1' or '10'."""
        if "+" in text:
            base_str, inc_str = text.split("+", 1)
            return cls(base_s=float(base_str), inc_s=float(inc_str))
        return cls(base_s=float(text), inc_s=0.0)

    def __str__(self) -> str:
        return f"{self.base_s:g}+{self.inc_s:g}"


class Clock:
    def __init__(self, base_s: float, inc_s: float) -> None:
        self.remaining_s = float(base_s)
        self.inc_s = float(inc_s)

    def spend(self, elapsed: float) -> bool:
        """Subtract elapsed time; return False if flagged, else add increment and return True."""
        self.remaining_s -= elapsed
        if self.remaining_s < 0:
            return False
        self.remaining_s += self.inc_s
        return True


@dataclass
class GameResult:
    white: str
    black: str
    opening: str
    result: str
    white_score: float
    termination: str
    plies: int
    pgn: str


def play_game(
    white_spec: EngineSpec,
    black_spec: EngineSpec,
    opening: str,
    tc: TimeControl,
    max_plies: int = 400,
) -> GameResult:
    """Play a single game between two engine specifications."""
    white_engine: chess.engine.SimpleEngine | None = None
    black_engine: chess.engine.SimpleEngine | None = None

    try:
        white_engine = chess.engine.SimpleEngine.popen_uci(white_spec.command, cwd=white_spec.cwd)
        if white_spec.options:
            white_engine.configure(white_spec.options)

        black_engine = chess.engine.SimpleEngine.popen_uci(black_spec.command, cwd=black_spec.cwd)
        if black_spec.options:
            black_engine.configure(black_spec.options)

        board = chess.Board()
        for move_uci in opening.split():
            board.push_uci(move_uci)

        white_clock = Clock(tc.base_s, tc.inc_s)
        black_clock = Clock(tc.base_s, tc.inc_s)

        result = "*"
        white_score = 0.5
        termination = ""

        with ThreadPoolExecutor(max_workers=1) as move_pool:
            while True:
                if board.is_game_over(claim_draw=True):
                    outcome = board.outcome(claim_draw=True)
                    if outcome is not None:
                        result = outcome.result()
                        if outcome.winner == chess.WHITE:
                            white_score = 1.0
                        elif outcome.winner == chess.BLACK:
                            white_score = 0.0
                        else:
                            white_score = 0.5
                        termination = outcome.termination.name
                    break

                if len(board.move_stack) >= max_plies:
                    result = "1/2-1/2"
                    white_score = 0.5
                    termination = "Max plies reached"
                    break

                is_white = board.turn == chess.WHITE
                curr_engine = white_engine if is_white else black_engine
                curr_spec = white_spec if is_white else black_spec
                curr_clock = white_clock if is_white else black_clock

                if curr_spec.limit is not None:
                    limit = chess.engine.Limit(**curr_spec.limit)
                    timeout = 30.0
                else:
                    limit = chess.engine.Limit(
                        white_clock=white_clock.remaining_s,
                        black_clock=black_clock.remaining_s,
                        white_inc=white_clock.inc_s,
                        black_inc=black_clock.inc_s,
                    )
                    timeout = max(0.1, curr_clock.remaining_s) + 10.0

                t0 = time.perf_counter()
                try:
                    fut = move_pool.submit(curr_engine.play, board, limit)
                    play_res = fut.result(timeout=timeout)
                    elapsed = time.perf_counter() - t0
                except Exception as err:
                    result = "0-1" if is_white else "1-0"
                    white_score = 0.0 if is_white else 1.0
                    termination = f"{curr_spec.name} error: {err}"
                    break

                move = play_res.move
                if move is None or move not in board.legal_moves:
                    result = "0-1" if is_white else "1-0"
                    white_score = 0.0 if is_white else 1.0
                    termination = f"Illegal move ({move}) by {curr_spec.name}"
                    break

                if curr_spec.limit is None:
                    if not curr_clock.spend(elapsed):
                        result = "0-1" if is_white else "1-0"
                        white_score = 0.0 if is_white else 1.0
                        termination = f"Time forfeit by {curr_spec.name}"
                        break

                board.push(move)

        pgn_game = chess.pgn.Game.from_board(board)
        pgn_game.headers["Event"] = "Harness Match"
        pgn_game.headers["White"] = white_spec.name
        pgn_game.headers["Black"] = black_spec.name
        pgn_game.headers["Result"] = result
        pgn_game.headers["Termination"] = termination
        pgn_game.headers["TimeControl"] = str(tc)
        pgn_game.headers["Opening"] = opening

        return GameResult(
            white=white_spec.name,
            black=black_spec.name,
            opening=opening,
            result=result,
            white_score=white_score,
            termination=termination,
            plies=len(board.move_stack),
            pgn=str(pgn_game),
        )

    finally:
        if white_engine is not None:
            try:
                white_engine.quit()
            except Exception:
                pass
        if black_engine is not None:
            try:
                black_engine.quit()
            except Exception:
                pass


def play_match(
    spec_a: EngineSpec,
    spec_b: EngineSpec,
    games: int,
    tc: TimeControl,
    concurrency: int = 1,
    max_plies: int = 400,
    openings: list[str] = OPENINGS,
) -> list[GameResult]:
    """Run a multi-game match between two engines with opening and color alternation."""
    tasks = []
    for i in range(games):
        opening = openings[(i // 2) % len(openings)]
        if i % 2 == 0:
            tasks.append((spec_a, spec_b, opening))
        else:
            tasks.append((spec_b, spec_a, opening))

    results: list[GameResult | None] = [None] * games
    workers = max(1, concurrency)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_idx = {
            executor.submit(play_game, w_spec, b_spec, op, tc, max_plies): idx
            for idx, (w_spec, b_spec, op) in enumerate(tasks)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            results[idx] = future.result()

    return [r for r in results if r is not None]
