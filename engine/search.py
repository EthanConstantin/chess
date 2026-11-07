"""Negamax search with alpha-beta pruning."""

import time
from dataclasses import dataclass

import chess

from engine.evaluation import evaluate

MATE_SCORE = 100_000
INF = 10 * MATE_SCORE


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

    def search(self, board: chess.Board, depth: int) -> SearchResult:
        """Search the position to a fixed depth.

        Resets node telemetry at each invocation so searches remain independent
        and deterministic.
        """
        self.nodes = 0
        start_time = time.perf_counter()

        score, pv = self._negamax(board, depth, -INF, INF, 0)
        move = pv[0] if pv else None
        elapsed = time.perf_counter() - start_time

        return SearchResult(
            move=move,
            score=score,
            pv=pv,
            depth=depth,
            nodes=self.nodes,
            time_s=elapsed,
        )

    def _negamax(
        self,
        board: chess.Board,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
    ) -> tuple[int, list[chess.Move]]:
        self.nodes += 1

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

        for move in ordered_moves(board):
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
            self.nodes += 1
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
