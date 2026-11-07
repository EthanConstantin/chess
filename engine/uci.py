"""Universal Chess Interface (UCI) protocol implementation."""

import math
import sys

import chess

from engine.search import MATE_SCORE, MAX_DEPTH, SearchResult, Searcher

DEFAULT_MOVETIME_S = 1.0
MIN_BUDGET_S = 0.02
SAFETY_MARGIN_S = 0.03


def format_score(score: int) -> str:
    """Format an engine score for UCI.

    UCI expects mate scores to be expressed in full moves to mate rather than
    centipawns, with negative numbers indicating the engine is getting mated.
    """
    if abs(score) >= MATE_SCORE - 1000:
        plies = MATE_SCORE - abs(score)
        moves = math.ceil(plies / 2)
        if score < 0:
            moves = -moves
        return f"score mate {moves}"
    return f"score cp {score}"


def parse_go_depth(tokens: list[str]) -> int:
    """Extract an explicit search depth from a go command, or MAX_DEPTH.

    Without a depth the search runs until its time budget ends; with neither a
    depth nor a clock, see parse_go_time.
    """
    value = _int_after(tokens, "depth")
    return value if value is not None and value > 0 else MAX_DEPTH


def parse_go_time(tokens: list[str], turn: chess.Color) -> float | None:
    """Work out how many seconds to spend on this move from a go command.

    `movetime` is used as given. With a clock, spend about 1/30 of the
    remaining time plus most of the increment: games last longer than 30
    moves, but the budget shrinks as the clock does, so it never runs out.
    A safety margin covers process and pipe overhead. Returns None when only
    a depth was given. A bare `go` (or `go infinite`, since `stop` is not
    supported) gets a default budget so it always answers.
    """
    movetime = _int_after(tokens, "movetime")
    if movetime is not None:
        return max(MIN_BUDGET_S, movetime / 1000 - SAFETY_MARGIN_S)

    remaining = _int_after(tokens, "wtime" if turn == chess.WHITE else "btime")
    if remaining is not None:
        increment = _int_after(tokens, "winc" if turn == chess.WHITE else "binc") or 0
        remaining_s, increment_s = remaining / 1000, increment / 1000
        budget = remaining_s / 30 + 0.8 * increment_s
        budget = min(budget, remaining_s / 4) - SAFETY_MARGIN_S
        return max(MIN_BUDGET_S, budget)

    if "depth" in tokens:
        return None
    return DEFAULT_MOVETIME_S


def _int_after(tokens: list[str], name: str) -> int | None:
    """Return the integer following `name` in tokens, if present and valid."""
    if name in tokens:
        idx = tokens.index(name)
        if idx + 1 < len(tokens):
            try:
                return int(tokens[idx + 1])
            except ValueError:
                return None
    return None


def apply_position(current_board: chess.Board, tokens: list[str]) -> chess.Board:
    """Set up the board from a UCI position command.

    Supports both 'startpos' and 'fen' specifications, followed by an optional
    sequence of moves.
    """
    if len(tokens) < 2:
        return current_board

    moves_idx = tokens.index("moves") if "moves" in tokens else len(tokens)

    if tokens[1] == "startpos":
        board = chess.Board()
        moves = tokens[moves_idx + 1:] if moves_idx < len(tokens) else []
    elif tokens[1] == "fen":
        fen_parts = tokens[2:moves_idx]
        fen_str = " ".join(fen_parts)
        moves = tokens[moves_idx + 1:] if moves_idx < len(tokens) else []
        try:
            board = chess.Board(fen_str)
        except ValueError:
            return current_board
    else:
        return current_board

    for move_str in moves:
        try:
            board.push_uci(move_str)
        except ValueError:
            break

    return board


def print_info(result: SearchResult) -> None:
    """Print a UCI info line for one completed search depth."""
    info_parts = [
        f"info depth {result.depth}",
        format_score(result.score),
        f"nodes {result.nodes}",
        f"time {int(result.time_s * 1000)}",
    ]
    if result.pv:
        info_parts.append(f"pv {' '.join(m.uci() for m in result.pv)}")
    print(" ".join(info_parts), flush=True)


def main() -> None:
    """Run the UCI protocol loop over standard input."""
    board = chess.Board()
    searcher = Searcher()

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        tokens = line.split()
        command = tokens[0]

        if command == "uci":
            print("id name Chess", flush=True)
            print("id author Ethan Constantin", flush=True)
            print("uciok", flush=True)
        elif command == "isready":
            print("readyok", flush=True)
        elif command == "ucinewgame":
            board = chess.Board()
        elif command == "position":
            board = apply_position(board, tokens)
        elif command == "go":
            depth = parse_go_depth(tokens)
            time_limit = parse_go_time(tokens, board.turn)
            result = searcher.search(board, depth, time_limit, on_iteration=print_info)
            if result.move is not None:
                print(f"bestmove {result.move.uci()}", flush=True)
            else:
                print("bestmove 0000", flush=True)
        elif command == "quit":
            break


if __name__ == "__main__":
    main()
