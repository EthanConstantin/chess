import math
import random

import pytest

from harness.rating import bootstrap_interval, expected_score, fit_ratings


def elo_from_score(p: float) -> float:
    return -400 * math.log10(1 / p - 1)


def test_expected_score():
    assert expected_score(1500, 1500) == pytest.approx(0.5)
    assert expected_score(1900, 1500) == pytest.approx(10 / 11)
    assert expected_score(1500, 1900) == pytest.approx(1 / 11)


def make_games(player, opponent, wins, draws, losses):
    """Games as (white, black, white_score). Colors alternate so color does not matter."""
    games = []
    results = [1.0] * wins + [0.5] * draws + [0.0] * losses
    for i, s in enumerate(results):
        if i % 2 == 0:
            games.append((player, opponent, s))
        else:
            games.append((opponent, player, 1.0 - s))
    return games


def test_single_anchor_mle_without_prior():
    games = make_games("engine", "anchor", wins=60, draws=30, losses=30)  # 75%
    ratings = fit_ratings(games, fixed={"anchor": 1500.0}, prior_draws=0.0)
    assert ratings["anchor"] == 1500.0
    assert ratings["engine"] == pytest.approx(1500 + elo_from_score(0.75), abs=1.0)


def test_two_anchors_mle_lies_between():
    games = make_games("engine", "low", wins=80, draws=0, losses=20)
    games += make_games("engine", "high", wins=20, draws=0, losses=80)
    ratings = fit_ratings(games, fixed={"low": 1300.0, "high": 1700.0}, prior_draws=0.0)
    assert ratings["engine"] == pytest.approx(1500.0, abs=1.0)


def test_prior_keeps_perfect_scores_finite():
    games = make_games("engine", "anchor", wins=0, draws=0, losses=50)
    ratings = fit_ratings(games, fixed={"anchor": 1320.0}, prior_draws=1.0)
    assert math.isfinite(ratings["engine"])
    assert ratings["engine"] < 1320.0 - 400


def test_pool_with_several_free_players():
    # a beats b 75%, b beats anchor 75%  ->  b ~ anchor+191, a ~ anchor+382
    games = make_games("a", "b", wins=150, draws=0, losses=50)
    games += make_games("b", "anchor", wins=150, draws=0, losses=50)
    ratings = fit_ratings(games, fixed={"anchor": 1000.0}, prior_draws=0.0)
    d = elo_from_score(0.75)
    assert ratings["b"] == pytest.approx(1000 + d, abs=2.0)
    assert ratings["a"] == pytest.approx(1000 + 2 * d, abs=3.0)


def test_bootstrap_interval_contains_estimate():
    rng = random.Random(1)
    results = [1.0 if rng.random() < 0.6 else 0.0 for _ in range(200)]
    games = [("engine", "anchor", s) for s in results]
    fixed = {"anchor": 1500.0}
    est = fit_ratings(games, fixed=fixed)["engine"]
    lo, hi = bootstrap_interval(games, fixed=fixed, player="engine", samples=200, seed=0)
    assert lo < est < hi
    assert 20 < hi - lo < 300  # 200 games gives roughly +-50 to +-70 Elo


def test_bootstrap_is_deterministic_for_a_seed():
    games = make_games("engine", "anchor", wins=30, draws=10, losses=20)
    fixed = {"anchor": 1500.0}
    a = bootstrap_interval(games, fixed=fixed, player="engine", samples=100, seed=7)
    b = bootstrap_interval(games, fixed=fixed, player="engine", samples=100, seed=7)
    assert a == b
