from harness.evaluations import render
from harness.match import GameResult, TimeControl, play_game
from harness.openings import OPENINGS
from harness.stats import classify_termination, move_stats, summarize
from harness.versions import anchor_spec


def game(white, black, white_score, termination="CHECKMATE", opening="e2e4 e7e5", plies=40,
         white_moves=None, black_moves=None):
    result = {1.0: "1-0", 0.5: "1/2-1/2", 0.0: "0-1"}[white_score]
    return GameResult(white, black, opening, result, white_score, termination, plies, "[Event]",
                      white_moves or [], black_moves or [])


def test_classify_termination():
    assert classify_termination(game("a", "b", 0.0, "Time forfeit by a")) == "TIME_FORFEIT"
    assert classify_termination(game("a", "b", 0.0, "a error: boom")) == "ENGINE_ERROR"
    assert classify_termination(game("a", "b", 0.0, "Illegal move (None) by a")) == "ILLEGAL_MOVE"
    assert classify_termination(game("a", "b", 0.5, "Max plies reached")) == "MAX_PLIES"
    assert classify_termination(game("a", "b", 0.5, "THREEFOLD_REPETITION")) == "THREEFOLD_REPETITION"


def test_summarize_from_player_perspective():
    games = [
        game("eng", "opp", 1.0),
        game("opp", "eng", 1.0, "Time forfeit by eng"),  # eng lost as black on time
        game("eng", "opp", 0.5, "THREEFOLD_REPETITION"),
        game("opp", "eng", 0.0),  # eng won as black
    ]
    s = summarize(games, "eng")
    assert s["overall"] == {"w": 2, "d": 1, "l": 1, "games": 4, "score_pct": 62.5}
    assert s["as_white"]["games"] == 2 and s["as_white"]["score_pct"] == 75.0
    assert s["as_black"]["w"] == 1 and s["as_black"]["l"] == 1
    assert s["endings"]["loss:TIME_FORFEIT"] == 1
    assert s["endings"]["win:CHECKMATE"] == 2
    assert s["endings"]["draw:THREEFOLD_REPETITION"] == 1
    assert s["by_opponent"]["opp"]["games"] == 4


def test_summarize_uses_only_own_moves():
    mine = [{"time_s": 0.1, "depth": 3, "nodes": 1000}]
    theirs = [{"time_s": 9.0, "depth": 20, "nodes": 10**7}]
    games = [game("eng", "opp", 1.0, white_moves=mine, black_moves=theirs),
             game("opp", "eng", 0.0, white_moves=theirs, black_moves=mine)]
    s = summarize(games, "eng")["search"]
    assert s["moves"] == 2 and s["depth_max"] == 3 and s["nodes_max"] == 1000
    assert s["nps_in_games"] == 10_000


def test_move_stats_handles_missing_info():
    s = move_stats([{"time_s": 0.2, "depth": None, "nodes": None}])
    assert s["moves"] == 1 and "depth_avg" not in s and "nodes_avg" not in s
    assert move_stats([]) == {"moves": 0}


def test_play_game_records_per_move_telemetry():
    tc = TimeControl(base_s=5.0, inc_s=0.05)
    g = play_game(anchor_spec("random"), anchor_spec("greedy"), OPENINGS[0], tc, max_plies=40)
    opening_plies = len(OPENINGS[0].split())
    assert len(g.white_moves) + len(g.black_moves) == g.plies - opening_plies or \
        g.termination.startswith(("Time", "Illegal")) or " error: " in g.termination
    assert all(m["time_s"] >= 0 for m in g.white_moves + g.black_moves)


def test_render_evaluations():
    games = [game("eng", "opp", 1.0, white_moves=[{"time_s": 0.1, "depth": 3, "nodes": 50}]),
             game("opp", "eng", 0.5, "THREEFOLD_REPETITION")]
    record = {
        "version": "v0.1-baseline", "label": "baseline", "sha": "abc123", "timestamp": "t",
        "env": {"cpu": "x", "cpu_count": 4, "platform": "p", "python": "3", "chess": "1", "stockfish": "sf"},
        "run": {"harness_sha": "def456", "duration_s": 12},
        "bench": {"depth": 2, "nodes": 10, "time_s": 1.0, "nps": 10,
                  "positions": [{"fen": "f", "nodes": 10, "time_s": 1.0, "nps": 10}]},
        "elo": {"rating": 1000, "ci_lo": 950, "ci_hi": 1050, "games": 2, "tc": "10+0.1",
                "opponents": {"opp": {"rating": 900}}, "stats": summarize(games, "eng")},
    }
    second = dict(record, version="v0.2", label="next", elo=dict(record["elo"], rating=1100))
    text = render([record, second])
    assert "# Evaluations" in text
    assert "## v0.1-baseline: baseline" in text and "## v0.2: next" in text
    assert "1000 (95% CI 950–1050)" in text
    assert "+100" in text
    assert "THREEFOLD_REPETITION" in text and "vs opp (900)" in text
