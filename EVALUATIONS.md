# Evaluations

Every engine version measured by the harness, newest last. Generated from
`telemetry/results.jsonl` by `python -m harness report`; do not edit by hand.
Methodology and caveats: [docs/BENCHMARKING.md](docs/BENCHMARKING.md).

| Version | Feature | Elo | Δ | Games |
|---|---|---|---|---|
| [v0.1-baseline](#v01-baseline-negamax--alpha-beta-material-eval-fixed-depth-3) | Negamax + alpha-beta, material eval, fixed depth 3 | 1075 ± 50 | - | 200 |

## v0.1-baseline: Negamax + alpha-beta, material eval, fixed depth 3

| | |
|---|---|
| **Estimated Elo** | **1075 (95% CI 1025–1125)** |
| Change vs previous version | - |
| Games / time control | 200 at 10+0.1 |
| Engine commit | `4bbd293f58` |
| Harness commit | `679c4ff230` |
| Recorded | 2026-11-02T18:22:05.939768+00:00 |
| Run duration | 182 s |
| Machine | Intel64 Family 6 Model 141 Stepping 1, GenuineIntel (16 threads), Windows-11-10.0.26200-SP0 |
| Software | Python 3.14.6, chess 1.11.2, Stockfish sf_19 |

### Results

| Split | W | D | L | Games | Score |
|---|---|---|---|---|---|
| Overall | 102 | 43 | 55 | 200 | 61.8% |
| As White | 52 | 20 | 29 | 101 | 61.4% |
| As Black | 50 | 23 | 26 | 99 | 62.1% |
| vs random (217) | 9 | 1 | 0 | 10 | 95.0% |
| vs greedy (697) | 80 | 15 | 0 | 95 | 92.1% |
| vs sf-1320-d1 (1230) | 13 | 27 | 55 | 95 | 27.9% |

### How games ended

| Outcome | Reason | Games |
|---|---|---|
| win | CHECKMATE | 102 |
| loss | CHECKMATE | 51 |
| draw | THREEFOLD_REPETITION | 43 |
| loss | TIME_FORFEIT | 4 |

Game length: avg 63.6 plies (min 13, max 195).

### Search behaviour in games

| Metric | Value |
|---|---|
| Moves searched | 5624 |
| Depth avg / min / max | 3.0 / 3 / 3 |
| Nodes per move avg / max | 3,546 / 28,962 |
| Time per move avg / median / p95 / max | 0.193 / 0.148 / 0.529 / 1.530 s |
| Nodes per second in games | 18,418 |

### Openings

| | Opening line | Score | Games |
|---|---|---|---|
| best | `e2e4 e7e5 b1c3 g8f6 f2f4 d7d5` | 87.5% | 4 |
| best | `e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6` | 78.6% | 14 |
| best | `d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7` | 75.0% | 8 |
| worst | `d2d4 d7d5 c1f4 g8f6 e2e3 c7c5` | 37.5% | 4 |
| worst | `e2e4 d7d6 d2d4 g8f6 b1c3 g7g6` | 37.5% | 4 |
| worst | `e2e4 e7e6 d2d4 d7d5 b1d2 g8f6` | 50.0% | 8 |

### Bench (fixed positions, depth 4)

| Position | Nodes | Time (s) | NPS |
|---|---|---|---|
| 1 | 1,516 | 0.037 | 40,448 |
| 2 | 62,642 | 1.720 | 36,410 |
| 3 | 52,179 | 2.357 | 22,141 |
| 4 | 87,153 | 3.223 | 27,037 |
| 5 | 1,998 | 0.071 | 28,039 |
| 6 | 246 | 0.009 | 27,751 |
| 7 | 6,679 | 0.220 | 30,366 |
| 8 | 150,230 | 4.962 | 30,274 |
| **Total** | **362,643** | **12.600** | **28,780** |

Games: `telemetry/games/elo_v0.1-baseline_20261102-182205.pgn`

---
