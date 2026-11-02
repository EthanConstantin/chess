"""Summary statistics for a set of games, from one player's point of view.

These numbers explain *why* Elo moved: how games end (time losses, repetition draws),
how deep the engine searches in real games, and how it uses its clock.
"""

import statistics
from collections import Counter

from harness.match import GameResult


def classify_termination(game: GameResult) -> str:
    """Normalize a termination string into a short category name."""
    t = game.termination
    if t.startswith("Time forfeit"):
        return "TIME_FORFEIT"
    if t.startswith("Illegal move"):
        return "ILLEGAL_MOVE"
    if " error: " in t:
        return "ENGINE_ERROR"
    if t.startswith("Max plies"):
        return "MAX_PLIES"
    return t or "UNKNOWN"


def _player_score(game: GameResult, player: str) -> float:
    return game.white_score if game.white == player else 1.0 - game.white_score


def _wdl(scores: list[float]) -> dict:
    n = len(scores)
    total = sum(scores)
    return {
        "w": scores.count(1.0),
        "d": scores.count(0.5),
        "l": scores.count(0.0),
        "games": n,
        "score_pct": round(100 * total / n, 1) if n else None,
    }


def _percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))
    return ordered[idx]


def move_stats(moves: list[dict]) -> dict:
    """Aggregate per-move search telemetry (time, depth, nodes)."""
    if not moves:
        return {"moves": 0}
    times = [m["time_s"] for m in moves]
    depths = [m["depth"] for m in moves if m.get("depth") is not None]
    nodes = [m["nodes"] for m in moves if m.get("nodes") is not None]
    total_time = sum(times)
    out = {
        "moves": len(moves),
        "time_avg_s": round(statistics.fmean(times), 4),
        "time_median_s": round(statistics.median(times), 4),
        "time_p95_s": round(_percentile(times, 95), 4),
        "time_max_s": round(max(times), 4),
    }
    if depths:
        out["depth_avg"] = round(statistics.fmean(depths), 2)
        out["depth_min"] = min(depths)
        out["depth_max"] = max(depths)
    if nodes:
        out["nodes_avg"] = round(statistics.fmean(nodes))
        out["nodes_max"] = max(nodes)
        out["nodes_total"] = sum(nodes)
        if total_time > 0:
            out["nps_in_games"] = round(sum(nodes) / total_time)
    return out


def summarize(games: list[GameResult], player: str) -> dict:
    """Full per-run statistics for `player` across `games`."""
    scores = [_player_score(g, player) for g in games]
    as_white = [_player_score(g, player) for g in games if g.white == player]
    as_black = [_player_score(g, player) for g in games if g.black == player]

    endings: Counter = Counter()
    for g, s in zip(games, scores):
        outcome = {1.0: "win", 0.5: "draw", 0.0: "loss"}[s]
        endings[f"{outcome}:{classify_termination(g)}"] += 1

    opponents: dict[str, list[float]] = {}
    openings: dict[str, list[float]] = {}
    for g, s in zip(games, scores):
        opp = g.black if g.white == player else g.white
        opponents.setdefault(opp, []).append(s)
        openings.setdefault(g.opening, []).append(s)

    plies = [g.plies for g in games]
    own_moves = [m for g in games for m in (g.white_moves if g.white == player else g.black_moves)]

    return {
        "overall": _wdl(scores),
        "as_white": _wdl(as_white),
        "as_black": _wdl(as_black),
        "endings": dict(sorted(endings.items(), key=lambda kv: -kv[1])),
        "game_length_plies": {
            "avg": round(statistics.fmean(plies), 1) if plies else None,
            "min": min(plies, default=None),
            "max": max(plies, default=None),
        },
        "search": move_stats(own_moves),
        "by_opponent": {k: _wdl(v) for k, v in opponents.items()},
        "by_opening": {k: _wdl(v) for k, v in openings.items()},
    }
