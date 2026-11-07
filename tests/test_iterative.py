import time

import chess

from engine.search import Searcher
from engine.uci import MIN_BUDGET_S, parse_go_depth, parse_go_time

MIDDLEGAME = "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 7"


def test_iterations_deepen_one_ply_at_a_time():
    depths = []
    result = Searcher().search(chess.Board(), depth=4, on_iteration=lambda r: depths.append(r.depth))
    assert depths == [1, 2, 3, 4]
    assert result.depth == 4


def test_time_limit_is_respected():
    board = chess.Board(MIDDLEGAME)
    start = time.perf_counter()
    result = Searcher().search(board, time_limit=0.5)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5 + 0.15  # deadline plus clock-check granularity
    assert result.depth >= 2
    assert result.move in board.legal_moves


def test_tiny_time_limit_still_returns_a_move():
    board = chess.Board(MIDDLEGAME)
    result = Searcher().search(board, time_limit=0.001)
    assert result.depth >= 1
    assert result.move in board.legal_moves


def test_board_restored_after_timeout():
    board = chess.Board(MIDDLEGAME)
    before = board.fen()
    Searcher().search(board, time_limit=0.2)  # aborts mid-iteration via an exception
    assert board.fen() == before
    assert not board.move_stack


def test_stops_early_on_forced_mate():
    result = Searcher().search(chess.Board("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"), depth=10)
    assert result.move == chess.Move.from_uci("a1a8")
    assert result.depth == 1


def test_parse_go_time():
    assert parse_go_time("go movetime 1000".split(), chess.WHITE) < 1.0
    assert parse_go_time("go depth 5".split(), chess.WHITE) is None
    assert parse_go_time("go".split(), chess.WHITE) > 0

    clock = "go wtime 30000 btime 1000 winc 0 binc 0".split()
    assert 0.5 < parse_go_time(clock, chess.WHITE) <= 1.0  # about 1/30 of 30 s
    assert parse_go_time(clock, chess.BLACK) < parse_go_time(clock, chess.WHITE)
    # Nearly flagged, the budget bottoms out at the minimum instead of going negative.
    assert parse_go_time("go wtime 10 btime 10".split(), chess.WHITE) == MIN_BUDGET_S


def test_parse_go_depth():
    assert parse_go_depth("go depth 5".split()) == 5
    assert parse_go_depth("go wtime 1000 btime 1000".split()) > 5
