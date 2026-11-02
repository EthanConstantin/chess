import chess
import pytest

from engine.evaluation import evaluate
from engine.search import MATE_SCORE, Searcher

# Positions verified by brute force in Python before these tests were written.
WHITE_MATE_IN_1 = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"  # Ra8#
BLACK_MATE_IN_1 = "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 0 1"  # Ra1#
WHITE_MATE_IN_2 = "7k/8/5K2/8/8/8/8/R7 w - - 0 1"  # no mate in 1, forced mate in 2
STALEMATE = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
BLACK_IS_MATED = "R5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 0 1"
FREE_QUEEN = "4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1"  # Rxd5 wins an undefended queen


def reference_minimax(board, depth, ply=0):
    """Plain negamax with no pruning. Alpha-beta must return exactly the same score."""
    if board.is_checkmate():
        return -(MATE_SCORE - ply)
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    if depth == 0:
        return evaluate(board)
    best = -10 * MATE_SCORE
    for move in list(board.legal_moves):
        board.push(move)
        best = max(best, -reference_minimax(board, depth - 1, ply + 1))
        board.pop()
    return best


@pytest.mark.parametrize("fen", [
    chess.STARTING_FEN,
    "rnbqkbnr/ppp1pppp/8/8/2pPP3/8/PP3PPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
    FREE_QUEEN,
])
def test_alpha_beta_matches_plain_minimax(fen):
    board = chess.Board(fen)
    result = Searcher().search(board, depth=3)
    assert result.score == reference_minimax(chess.Board(fen), 3)


def test_alpha_beta_prunes():
    """With a correct window, alpha-beta searches far fewer nodes than full minimax."""
    board = chess.Board()
    result = Searcher().search(board, depth=4)
    assert result.nodes < 197_281 // 2  # perft(4) leaf count from the start position


@pytest.mark.parametrize("fen,expected", [
    (WHITE_MATE_IN_1, "a1a8"),
    (BLACK_MATE_IN_1, "a8a1"),
])
def test_finds_mate_in_1(fen, expected):
    result = Searcher().search(chess.Board(fen), depth=2)
    assert result.move == chess.Move.from_uci(expected)
    assert result.score == MATE_SCORE - 1


def test_finds_mate_in_2():
    board = chess.Board(WHITE_MATE_IN_2)
    result = Searcher().search(board, depth=3)
    assert result.score == MATE_SCORE - 3
    board.push(result.move)
    assert not board.is_checkmate()  # there is no mate in 1, so the first move is quiet


def test_prefers_faster_mate():
    # Mate in 1 is available, so the score must reflect mate in 1 even at a deeper depth.
    result = Searcher().search(chess.Board(WHITE_MATE_IN_1), depth=4)
    assert result.score == MATE_SCORE - 1


def test_stalemate_scores_zero():
    result = Searcher().search(chess.Board(STALEMATE), depth=3)
    assert result.score == 0
    assert result.move is None


def test_checkmated_side_has_no_move():
    result = Searcher().search(chess.Board(BLACK_IS_MATED), depth=3)
    assert result.move is None
    assert result.score == -MATE_SCORE


def test_takes_free_queen():
    result = Searcher().search(chess.Board(FREE_QUEEN), depth=2)
    assert result.move == chess.Move.from_uci("d1d5")


def test_search_does_not_change_board():
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
    before = board.fen()
    Searcher().search(board, depth=3)
    assert board.fen() == before
    assert len(board.move_stack) == 0


def test_result_fields():
    board = chess.Board()
    result = Searcher().search(board, depth=2)
    assert result.move in board.legal_moves
    assert result.depth == 2
    assert result.nodes > 0
    assert result.time_s >= 0
    assert result.pv and result.pv[0] == result.move
    # The principal variation must be a legal sequence of moves.
    replay = board.copy()
    for move in result.pv:
        assert move in replay.legal_moves
        replay.push(move)


def test_node_count_resets_between_searches():
    searcher = Searcher()
    first = searcher.search(chess.Board(), depth=2).nodes
    second = searcher.search(chess.Board(), depth=2).nodes
    assert first == second
