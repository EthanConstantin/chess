import chess
import pytest

from engine.evaluation import evaluate
from engine.search import MATE_SCORE, Searcher

# Qxd5 wins a pawn at depth 1, but exd5 wins the queen back.
POISONED_PAWN = "4k3/8/4p3/3p4/8/8/8/3QK3 w - - 0 1"
# Rxd5 wins an undefended queen.
FREE_QUEEN = "4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1"


def reference_quiesce(board, ply):
    """Quiescence with no pruning: stand pat or capture, all evasions in check."""
    if board.is_check():
        moves = list(board.legal_moves)
        if not moves:
            return -(MATE_SCORE - ply)
        best = -10 * MATE_SCORE
    else:
        best = evaluate(board)
        moves = list(board.generate_legal_captures())
    for move in moves:
        board.push(move)
        best = max(best, -reference_quiesce(board, ply + 1))
        board.pop()
    return best


def reference_search(board, depth, ply=0):
    """Plain negamax ending in unpruned quiescence. Alpha-beta must match it exactly."""
    if board.is_checkmate():
        return -(MATE_SCORE - ply)
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    if depth == 0:
        return reference_quiesce(board, ply)
    best = -10 * MATE_SCORE
    for move in list(board.legal_moves):
        board.push(move)
        best = max(best, -reference_search(board, depth - 1, ply + 1))
        board.pop()
    return best


@pytest.mark.parametrize("fen,depth", [
    (POISONED_PAWN, 2),
    (FREE_QUEEN, 2),
    # Small positions with exchanges: the unpruned reference explodes on a full board.
    ("r3k3/1p3p2/2n1b3/3pP3/3N4/2B5/1P3P2/R3K3 w - - 0 1", 2),
    ("2r3k1/5ppp/2n5/3p4/3P4/2N2B2/5PPP/2R3K1 w - - 0 1", 2),
    ("6k1/5p1p/4b1p1/3p4/3N4/2P3P1/5P1P/6K1 w - - 0 1", 3),
])
def test_quiescence_matches_unpruned_reference(fen, depth):
    result = Searcher().search(chess.Board(fen), depth=depth)
    assert result.score == reference_search(chess.Board(fen), depth)


def test_avoids_poisoned_pawn():
    """Without quiescence, depth 1 grabs the pawn and loses the queen."""
    board = chess.Board(POISONED_PAWN)
    qxd5 = chess.Move.from_uci("d1d5")
    assert Searcher(quiescence=False).search(board, depth=1).move == qxd5
    assert Searcher().search(board, depth=1).move != qxd5


def test_resolves_exchange_at_horizon():
    """At depth 1 the free queen is still taken, and the score reflects it."""
    result = Searcher().search(chess.Board(FREE_QUEEN), depth=1)
    assert result.move == chess.Move.from_uci("d1d5")
    assert result.score == 500  # rook vs bare king after the capture

