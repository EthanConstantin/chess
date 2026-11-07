"""Negamax alpha-beta search with move ordering, quiescence and iterative deepening."""

import time
from collections.abc import Callable
from dataclasses import dataclass

import chess

from engine.evaluation import evaluate

MATE_SCORE = 100_000
INF = 10 * MATE_SCORE
MAX_DEPTH = 64
# The clock is read once per this many nodes: often enough to stop within a few
# milliseconds of the deadline, rarely enough to cost nothing measurable.
TIME_CHECK_INTERVAL = 256


class SearchTimeout(Exception):
    """Raised inside the search when the time budget runs out."""


def move_order_key(board: chess.Board, move: chess.Move) -> int:
    """Score a move for ordering: higher is searched first.

    Alpha-beta prunes most when the best move is tried first. Captures are the
    likeliest refutations, so they go first, ordered MVV-LVA (most valuable
    victim, then least valuable attacker): PxQ before QxP. Promotions are
    treated like captures of the promoted piece. Quiet moves keep generator order.
    """
    score = 0
    if board.is_capture(move):
        # En passant lands on an empty square; the victim is always a pawn.
        victim = board.piece_type_at(move.to_square) or chess.PAWN
        attacker = board.piece_type_at(move.from_square)
        score += 1_000 + 10 * victim - attacker
    if move.promotion:
        score += 1_000 + 10 * move.promotion
    return score


def ordered_moves(board: chess.Board) -> list[chess.Move]:
    """Return the legal moves, best-first by move_order_key."""
    return sorted(board.legal_moves, key=lambda m: move_order_key(board, m), reverse=True)


@dataclass(frozen=True)
class SearchResult:
    move: chess.Move | None
    score: int
    pv: list[chess.Move]
    depth: int
    nodes: int
    time_s: float


class Searcher:
    """Performs alpha-beta minimax search without module-level state."""

    def __init__(self, quiescence: bool = True) -> None:
        # quiescence=False gives plain fixed-depth alpha-beta; tests use it to
        # compare against reference minimax.
        self.quiescence = quiescence
        self.nodes: int = 0
        self._deadline: float | None = None
        self._root_first: chess.Move | None = None

    def search(
        self,
        board: chess.Board,
        depth: int = MAX_DEPTH,
        time_limit: float | None = None,
        on_iteration: Callable[[SearchResult], None] | None = None,
    ) -> SearchResult:
        """Search with iterative deepening, up to `depth` plies or `time_limit` seconds.

        Searching depth 1, 2, 3, ... looks wasteful, but each pass is much
        cheaper than the next, and its best move is searched first in the next
        pass, which makes alpha-beta cut off sooner. It also means a move is
        always ready: when time runs out mid-iteration, that iteration is thrown
        away and the last completed one is returned. Depth 1 always completes.

        `on_iteration` is called after each completed depth (UCI prints info).
        Node telemetry is reset per call so searches stay independent.
        """
        self.nodes = 0
        self._deadline = None
        self._root_first = None
        start_time = time.perf_counter()
        result: SearchResult | None = None

        for current_depth in range(1, depth + 1):
            try:
                score, pv = self._negamax(board, current_depth, -INF, INF, 0)
            except SearchTimeout:
                break

            elapsed = time.perf_counter() - start_time
            result = SearchResult(
                move=pv[0] if pv else None,
                score=score,
                pv=pv,
                depth=current_depth,
                nodes=self.nodes,
                time_s=elapsed,
            )
            if on_iteration is not None:
                on_iteration(result)

            self._root_first = result.move
            if result.move is None or abs(score) >= MATE_SCORE - current_depth:
                break  # no legal moves, or a mate within the horizon: deeper cannot improve it
            if time_limit is not None:
                # The next iteration costs several times this one, so starting it
                # past half the budget would most likely be wasted.
                if elapsed > time_limit / 2:
                    break
                self._deadline = start_time + time_limit

        assert result is not None  # depth >= 1 and depth 1 never times out
        return result

    def _count_node(self) -> None:
        """Count a node and abort the search if the deadline has passed."""
        self.nodes += 1
        if (
            self._deadline is not None
            and self.nodes % TIME_CHECK_INTERVAL == 0
            and time.perf_counter() > self._deadline
        ):
            raise SearchTimeout

    def _negamax(
        self,
        board: chess.Board,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
    ) -> tuple[int, list[chess.Move]]:
        self._count_node()

        # Check terminal states before depth==0 so mate at the search horizon is detected.
        if board.is_checkmate():
            return -(MATE_SCORE - ply), []
        if board.is_stalemate() or board.is_insufficient_material():
            return 0, []
        if depth == 0:
            if self.quiescence:
                return self._quiesce(board, alpha, beta, ply), []
            return evaluate(board), []

        best_score = -INF
        best_line: list[chess.Move] = []

        moves = ordered_moves(board)
        if ply == 0 and self._root_first in moves:
            # Best move from the previous iteration goes first.
            moves.remove(self._root_first)
            moves.insert(0, self._root_first)

        for move in moves:
            board.push(move)
            try:
                score, line = self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
                score = -score
            finally:
                board.pop()

            if score > best_score:
                best_score = score
                best_line = [move] + line

            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        return best_score, best_line

    def _quiesce(self, board: chess.Board, alpha: int, beta: int, ply: int) -> int:
        """Search captures until the position is quiet, then evaluate.

        A fixed-depth search stops wherever the depth runs out, even halfway
        through an exchange, so QxP looks like a free pawn when PxQ comes next.
        Following captures to the end removes this horizon effect. The side to
        move may also decline every capture ("stand pat"), so the static
        evaluation is a lower bound. In check there is no standing pat: every
        evasion is searched, which also lets quiescence see checkmates.

        The node that calls this was already counted by _negamax, so nodes are
        counted as each capture is made rather than on entry.
        """
        in_check = board.is_check()
        if in_check:
            best_score = -INF
            moves = ordered_moves(board)
            if not moves:
                return -(MATE_SCORE - ply)
        else:
            best_score = evaluate(board)
            if best_score >= beta:
                return best_score
            alpha = max(alpha, best_score)
            moves = sorted(
                board.generate_legal_captures(),
                key=lambda m: move_order_key(board, m),
                reverse=True,
            )

        for move in moves:
            self._count_node()
            board.push(move)
            try:
                score = -self._quiesce(board, -beta, -alpha, ply + 1)
            finally:
                board.pop()

            if score > best_score:
                best_score = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        return best_score
