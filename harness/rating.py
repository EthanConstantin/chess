"""Elo rating calculation, maximum-likelihood fitting and bootstrapping.

Elo is relative: ratings are estimated on a Bradley-Terry logistic model
against a reference pool of fixed anchor ratings.
"""

import collections
import math
import random


def expected_score(ra: float, rb: float) -> float:
    """Return the expected score of player A against player B under the logistic model."""
    return 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))


def fit_ratings(
    games: list[tuple[str, str, float]],
    fixed: dict[str, float],
    prior_draws: float = 1.0,
) -> dict[str, float]:
    """Fit maximum-likelihood ratings for all players given game results and fixed anchors.

    Draws count as half a win. Virtual draws are added for every pair that met to keep
    extreme scores finite.
    """
    players: set[str] = set(fixed.keys())
    pairs: set[tuple[str, str]] = set()

    # Track scores: W[u][v] is score won by u against v
    W: dict[str, dict[str, float]] = collections.defaultdict(lambda: collections.defaultdict(float))

    for white, black, white_score in games:
        players.add(white)
        players.add(black)
        u, v = sorted((white, black))
        pairs.add((u, v))
        W[white][black] += white_score
        W[black][white] += 1.0 - white_score

    if prior_draws > 0:
        for u, v in pairs:
            W[u][v] += 0.5 * prior_draws
            W[v][u] += 0.5 * prior_draws

    free_players = [p for p in players if p not in fixed]
    if not free_players:
        return {p: float(fixed[p]) for p in players}

    init_val = (sum(fixed.values()) / len(fixed)) if fixed else 1500.0
    ratings: dict[str, float] = {p: float(fixed[p]) for p in fixed}
    for p in free_players:
        ratings[p] = init_val

    c = math.log(10.0) / 400.0

    for _ in range(2000):
        max_change = 0.0
        for p in free_players:
            actual_sum = 0.0
            exp_sum = 0.0
            deriv = 0.0
            for opp in players:
                if opp == p:
                    continue
                n = W[p][opp] + W[opp][p]
                if n == 0:
                    continue
                exp_p = expected_score(ratings[p], ratings[opp])
                actual_sum += W[p][opp]
                exp_sum += n * exp_p
                deriv += n * exp_p * (1.0 - exp_p)

            if deriv > 0:
                step = (actual_sum - exp_sum) / (c * deriv)
            else:
                step = 0.0

            # Dampen step to prevent wild oscillation
            if step > 200.0:
                step = 200.0
            elif step < -200.0:
                step = -200.0

            ratings[p] += step
            if abs(step) > max_change:
                max_change = abs(step)

        if not fixed:
            # Preserve mean rating at 1500 if no fixed anchor
            mean_diff = (sum(ratings.values()) / len(ratings)) - 1500.0
            for p in free_players:
                ratings[p] -= mean_diff

        if max_change < 0.01:
            break

    return ratings


def bootstrap_interval(
    games: list[tuple[str, str, float]],
    fixed: dict[str, float],
    player: str,
    samples: int = 500,
    seed: int = 0,
    prior_draws: float = 1.0,
    level: float = 0.95,
) -> tuple[float, float]:
    """Calculate a percentile confidence interval for a player's rating via resampling."""
    if not games:
        val = fixed.get(player, 1500.0)
        return val, val

    rng = random.Random(seed)
    n = len(games)
    estimates = []
    for _ in range(samples):
        resample = rng.choices(games, k=n)
        fitted = fit_ratings(resample, fixed=fixed, prior_draws=prior_draws)
        estimates.append(fitted[player])

    estimates.sort()
    alpha = (1.0 - level) / 2.0
    lo_idx = int(alpha * samples)
    hi_idx = min(samples - 1, int((1.0 - alpha) * samples))
    return estimates[lo_idx], estimates[hi_idx]
