import chess
import pytest

from engine.search import MATE_SCORE, Searcher, score_from_tt, score_to_tt

PAWN_ENDING = "8/5p2/4p1p1/4k2p/7P/4K1P1/5P2/8 w - - 0 40"
WHITE_MATE_IN_2 = "7k/8/5K2/8/8/8/8/R7 w - - 0 1"


class NoTable(dict):
    """A transposition table that never stores anything, to measure the real one."""

    def __setitem__(self, key, value):
        pass


def search_without_table(fen, depth):
    searcher = Searcher()
    searcher._tt = NoTable()
    return searcher.search(chess.Board(fen), depth=depth)


def test_table_reduces_nodes():
    # Measured: 12,360 nodes with the table vs 18,868 without at depth 5.
    with_table = Searcher().search(chess.Board(), depth=5)
    without_table = search_without_table(chess.STARTING_FEN, depth=5)
    assert with_table.score == without_table.score
    assert with_table.nodes < 0.8 * without_table.nodes


@pytest.mark.parametrize("fen", [
    chess.STARTING_FEN,
    "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 7",
    PAWN_ENDING,
])
def test_table_does_not_change_score_at_depth_3(fen):
    """No position can repeat within 3 plies, so the table must not change the score."""
    assert Searcher().search(chess.Board(fen), depth=3).score == search_without_table(fen, 3).score


def test_mate_distance_survives_the_table():
    # Deep enough that table entries are reused at different plies.
    result = Searcher().search(chess.Board(WHITE_MATE_IN_2), depth=5)
    assert result.score == MATE_SCORE - 3


def test_mate_score_round_trip():
    for score in (MATE_SCORE - 7, -(MATE_SCORE - 7), 250, -250, 0):
        for ply in (0, 1, 6):
            assert score_from_tt(score_to_tt(score, ply), ply) == score
    # A mate 7 plies from the root, seen 4 plies in, is a mate in 3 plies from that node.
    assert score_to_tt(MATE_SCORE - 7, 4) == MATE_SCORE - 3


def test_table_is_reset_between_searches():
    searcher = Searcher()
    first = searcher.search(chess.Board(PAWN_ENDING), depth=4).nodes
    second = searcher.search(chess.Board(PAWN_ENDING), depth=4).nodes
    assert first == second
