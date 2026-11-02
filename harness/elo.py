"""Elo estimation by adaptive anchor probing and bracketed matches.

Probes the anchor ladder to bracket the engine's playing strength, runs a
focused match between the two bounding anchors, and estimates Elo via MLE.
"""

import json
import os

from harness.match import TimeControl, play_match
from harness.rating import bootstrap_interval, fit_ratings
from harness.telemetry import ANCHORS_PATH, save_pgn
from harness.versions import ANCHOR_LADDER, EngineSpec, anchor_spec


def estimate_elo(
    spec: EngineSpec,
    games: int = 200,
    tc: TimeControl | str = "10+0.1",
    concurrency: int | None = None,
    probe_games: int = 10,
) -> dict:
    """Estimate Elo rating against calibrated anchor ladder."""
    if isinstance(tc, str):
        tc = TimeControl.parse(tc)
    if concurrency is None:
        concurrency = max(1, (os.cpu_count() or 2) // 2)

    if not ANCHORS_PATH.exists():
        raise RuntimeError("Anchor ratings file not found. Run 'python -m harness calibrate' first.")

    anchors_file = json.loads(ANCHORS_PATH.read_text(encoding="utf-8"))
    ratings_data = anchors_file.get("ratings", {})

    missing_anchors = [a.name for a in ANCHOR_LADDER if a.name not in ratings_data]
    if missing_anchors:
        raise RuntimeError(
            f"Missing ratings for {missing_anchors}. Run 'python -m harness calibrate' first."
        )

    all_game_results = []
    crossed_idx = len(ANCHOR_LADDER)

    # 1. Probe phase: walk from weakest anchor upwards
    for i, anchor in enumerate(ANCHOR_LADDER):
        opp_spec = anchor_spec(anchor.name)
        probe_match = play_match(
            spec,
            opp_spec,
            games=probe_games,
            tc=tc,
            concurrency=concurrency,
        )
        all_game_results.extend(probe_match)

        score = sum(
            g.white_score if g.white == spec.name else 1.0 - g.white_score
            for g in probe_match
        )
        print(f"Probe vs {anchor.name}: {score:.1f}/{probe_games} ({score / probe_games:.1%})")

        if score < 0.5 * probe_games:
            crossed_idx = i
            break

    # 2. Main phase: bracket selection
    if crossed_idx == 0:
        bracket = (ANCHOR_LADDER[0], ANCHOR_LADDER[1])
    elif crossed_idx >= len(ANCHOR_LADDER):
        bracket = (ANCHOR_LADDER[-2], ANCHOR_LADDER[-1])
    else:
        bracket = (ANCHOR_LADDER[crossed_idx - 1], ANCHOR_LADDER[crossed_idx])

    remaining_games = max(0, games - len(all_game_results))
    games_a = remaining_games // 2
    games_b = remaining_games - games_a

    if games_a > 0:
        match_a = play_match(
            spec,
            anchor_spec(bracket[0].name),
            games=games_a,
            tc=tc,
            concurrency=concurrency,
        )
        all_game_results.extend(match_a)
        score_a = sum(
            g.white_score if g.white == spec.name else 1.0 - g.white_score
            for g in match_a
        )
        print(f"Main vs {bracket[0].name}: {score_a:.1f}/{games_a} ({score_a / games_a:.1%})")

    if games_b > 0:
        match_b = play_match(
            spec,
            anchor_spec(bracket[1].name),
            games=games_b,
            tc=tc,
            concurrency=concurrency,
        )
        all_game_results.extend(match_b)
        score_b = sum(
            g.white_score if g.white == spec.name else 1.0 - g.white_score
            for g in match_b
        )
        print(f"Main vs {bracket[1].name}: {score_b:.1f}/{games_b} ({score_b / games_b:.1%})")

    # 3. Fit ratings and bootstrap confidence interval
    fixed = {name: float(info["rating"]) for name, info in ratings_data.items()}
    rating_games = [(g.white, g.black, g.white_score) for g in all_game_results]
    fitted = fit_ratings(rating_games, fixed=fixed)
    spec_rating = fitted[spec.name]
    ci_lo, ci_hi = bootstrap_interval(rating_games, fixed=fixed, player=spec.name)

    # 4. Compile opponents record
    opponents: dict[str, dict] = {}
    for g in all_game_results:
        opp_name = g.black if g.white == spec.name else g.white
        spec_won = (
            (g.white == spec.name and g.white_score == 1.0)
            or (g.black == spec.name and g.white_score == 0.0)
        )
        spec_drew = g.white_score == 0.5
        spec_lost = (
            (g.white == spec.name and g.white_score == 0.0)
            or (g.black == spec.name and g.white_score == 1.0)
        )

        if opp_name not in opponents:
            opponents[opp_name] = {
                "rating": ratings_data[opp_name]["rating"],
                "w": 0,
                "d": 0,
                "l": 0,
            }

        if spec_won:
            opponents[opp_name]["w"] += 1
        elif spec_drew:
            opponents[opp_name]["d"] += 1
        elif spec_lost:
            opponents[opp_name]["l"] += 1

    pgn_path = str(save_pgn(all_game_results, f"elo_{spec.name}"))

    return {
        "rating": spec_rating,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "games": len(all_game_results),
        "tc": str(tc),
        "opponents": opponents,
        "pgn_path": pgn_path,
    }
