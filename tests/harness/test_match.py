import chess
import pytest

from harness.match import Clock, TimeControl, play_game, play_match
from harness.openings import OPENINGS
from harness.versions import anchor_spec


def test_time_control_parse():
    tc = TimeControl.parse("10+0.1")
    assert tc.base_s == 10.0 and tc.inc_s == 0.1
    assert str(tc) == "10+0.1"


def test_clock_spends_and_increments():
    clock = Clock(base_s=1.0, inc_s=0.5)
    assert clock.spend(0.4) is True  # still has time
    assert clock.remaining_s == pytest.approx(1.1)
    assert clock.spend(5.0) is False  # flagged


def test_openings_are_legal_and_unique():
    assert len(OPENINGS) >= 20
    assert len(set(OPENINGS)) == len(OPENINGS)
    for line in OPENINGS:
        board = chess.Board()
        moves = line.split()
        assert 4 <= len(moves) <= 12
        for uci in moves:
            move = chess.Move.from_uci(uci)
            assert move in board.legal_moves, line
            board.push(move)


def test_play_game_random_vs_greedy():
    tc = TimeControl(base_s=5.0, inc_s=0.05)
    game = play_game(anchor_spec("random"), anchor_spec("greedy"), OPENINGS[0], tc, max_plies=120)
    assert game.white == "random" and game.black == "greedy"
    assert game.result in ("1-0", "0-1", "1/2-1/2")
    assert game.white_score in (0.0, 0.5, 1.0)
    assert game.termination
    assert game.plies >= len(OPENINGS[0].split())
    assert game.pgn.startswith("[Event")


def test_play_game_respects_max_plies():
    tc = TimeControl(base_s=5.0, inc_s=0.05)
    game = play_game(anchor_spec("random"), anchor_spec("random"), OPENINGS[1], tc, max_plies=20)
    assert game.plies <= 20
    if game.plies == 20:
        assert game.result == "1/2-1/2"


def test_play_match_alternates_colors_and_openings():
    tc = TimeControl(base_s=5.0, inc_s=0.05)
    games = play_match(anchor_spec("random"), anchor_spec("greedy"), games=4, tc=tc,
                       concurrency=2, max_plies=60)
    assert len(games) == 4
    assert [g.white for g in games] == ["random", "greedy", "random", "greedy"]
    assert games[0].opening == games[1].opening == OPENINGS[0]
    assert games[2].opening == games[3].opening == OPENINGS[1]


def test_greedy_beats_random_more_often():
    tc = TimeControl(base_s=5.0, inc_s=0.05)
    games = play_match(anchor_spec("greedy"), anchor_spec("random"), games=6, tc=tc,
                       concurrency=3, max_plies=200)
    greedy_score = sum(g.white_score if g.white == "greedy" else 1 - g.white_score for g in games)
    assert greedy_score > 3
