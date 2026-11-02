"""Anchor ladder calibration.

Plays head-to-head matches between adjacent free anchors and links them
to the fixed Stockfish rating ladder.
"""

from datetime import datetime, timezone
import json
import os

from harness.match import TimeControl, play_match
from harness.rating import bootstrap_interval, fit_ratings
from harness.stockfish import STOCKFISH_TAG
from harness.telemetry import ANCHORS_PATH, save_pgn
from harness.versions import ANCHOR_LADDER, anchor_spec


def calibrate(
    games_per_pair: int = 40,
    tc: TimeControl | str = "10+0.1",
    concurrency: int | None = None,
) -> dict:
    """Calibrate ratings for all free anchors and write telemetry/anchors.json."""
    if isinstance(tc, str):
        tc = TimeControl.parse(tc)
    if concurrency is None:
        concurrency = max(1, (os.cpu_count() or 2) // 2)

    pairs_to_play = []
    for i in range(len(ANCHOR_LADDER) - 1):
        a = ANCHOR_LADDER[i]
        b = ANCHOR_LADDER[i + 1]
        if a.fixed_rating is None or b.fixed_rating is None:
            pairs_to_play.append((a, b))

    all_game_results = []
    for a, b in pairs_to_play:
        print(f"Calibrating pair {a.name} vs {b.name} ({games_per_pair} games)...")
        spec_a = anchor_spec(a.name)
        spec_b = anchor_spec(b.name)
        results = play_match(
            spec_a,
            spec_b,
            games=games_per_pair,
            tc=tc,
            concurrency=concurrency,
        )
        all_game_results.extend(results)

    fixed = {a.name: float(a.fixed_rating) for a in ANCHOR_LADDER if a.fixed_rating is not None}
    rating_games = [(g.white, g.black, g.white_score) for g in all_game_results]
    fitted = fit_ratings(rating_games, fixed=fixed)

    ratings_dict = {}
    for a in ANCHOR_LADDER:
        if a.fixed_rating is not None:
            r = float(a.fixed_rating)
            ratings_dict[a.name] = {"rating": r, "ci_lo": r, "ci_hi": r}
        else:
            r = fitted[a.name]
            lo, hi = bootstrap_interval(rating_games, fixed=fixed, player=a.name)
            ratings_dict[a.name] = {"rating": r, "ci_lo": lo, "ci_hi": hi}

    data = {
        "meta": {
            "stockfish": STOCKFISH_TAG,
            "tc": str(tc),
            "games_per_pair": games_per_pair,
            "date": datetime.now(timezone.utc).isoformat(),
        },
        "ratings": ratings_dict,
    }

    ANCHORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ANCHORS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    save_pgn(all_game_results, "calibrate")

    print("\nAnchor Calibration Results:")
    print(f"{'Anchor':<15} {'Rating':>8}   {'95% CI':>16}")
    print("-" * 45)
    for name, info in ratings_dict.items():
        r = info["rating"]
        lo = info["ci_lo"]
        hi = info["ci_hi"]
        ci_str = "(fixed)" if lo == hi else f"[{lo:.1f}, {hi:.1f}]"
        print(f"{name:<15} {r:>8.1f}   {ci_str:>16}")

    return data
