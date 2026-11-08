# Evaluations

Every engine version measured by the harness, newest last. Generated from
`telemetry/results.jsonl` by `python -m harness report`; do not edit by hand.
Methodology and caveats: [docs/BENCHMARKING.md](docs/BENCHMARKING.md).

| Version | Feature | Elo | Δ | Games |
|---|---|---|---|---|
| [v0.1-baseline](#v01-baseline-negamax--alpha-beta-material-eval-fixed-depth-3) | Negamax + alpha-beta, material eval, fixed depth 3 | 1075 ± 50 | - | 200 |
| [v0.2-move-ordering](#v02-move-ordering-mvv-lva-move-ordering) | MVV-LVA move ordering | 1084 ± 46 | +9 | 200 |
| [v0.3-quiescence](#v03-quiescence-quiescence-search) | Quiescence search | 1147 ± 49 | +63 | 200 |
| [v0.4-iterative-deepening](#v04-iterative-deepening-iterative-deepening--time-management) | Iterative deepening + time management | 1206 ± 44 | +59 | 200 |
| [v0.5-transposition-table](#v05-transposition-table-transposition-table) | Transposition table | 1171 ± 49 | -35 | 200 |

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

## v0.2-move-ordering: MVV-LVA move ordering

| | |
|---|---|
| **Estimated Elo** | **1084 (95% CI 1037–1129)** |
| Change vs previous version | +9 |
| Games / time control | 200 at 10+0.1 |
| Engine commit | `013d6f17d7` |
| Harness commit | `013d6f17d7` |
| Recorded | 2026-11-07T23:31:41.164564+00:00 |
| Run duration | 94 s |
| Machine | Intel64 Family 6 Model 141 Stepping 1, GenuineIntel (16 threads), Windows-11-10.0.26200-SP0 |
| Software | Python 3.14.6, chess 1.11.2, Stockfish sf_19 |

### Results

| Split | W | D | L | Games | Score |
|---|---|---|---|---|---|
| Overall | 94 | 62 | 44 | 200 | 62.5% |
| As White | 50 | 28 | 23 | 101 | 63.4% |
| As Black | 44 | 34 | 21 | 99 | 61.6% |
| vs random (217) | 10 | 0 | 0 | 10 | 100.0% |
| vs greedy (697) | 75 | 20 | 0 | 95 | 89.5% |
| vs sf-1320-d1 (1230) | 9 | 42 | 44 | 95 | 31.6% |

### How games ended

| Outcome | Reason | Games |
|---|---|---|
| win | CHECKMATE | 94 |
| draw | THREEFOLD_REPETITION | 62 |
| loss | CHECKMATE | 44 |

Game length: avg 69.4 plies (min 12, max 240).

### Search behaviour in games

| Metric | Value |
|---|---|
| Moves searched | 6210 |
| Depth avg / min / max | 3.0 / 3 / 3 |
| Nodes per move avg / max | 1,239 / 8,475 |
| Time per move avg / median / p95 / max | 0.083 / 0.077 / 0.182 / 0.678 s |
| Nodes per second in games | 14,896 |

### Openings

| | Opening line | Score | Games |
|---|---|---|---|
| best | `e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6` | 75.0% | 8 |
| best | `e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 b8c6` | 75.0% | 8 |
| best | `d2d4 d7d5 c2c4 c7c6 g1f3 g8f6 b1c3 d5c4` | 75.0% | 8 |
| worst | `c2c4 e7e5 b1c3 g8f6 g1f3 b8c6` | 37.5% | 4 |
| worst | `e2e4 c7c6 d2d4 d7d5 e4e5 c8f5` | 43.8% | 8 |
| worst | `e2e4 c7c6 d2d4 d7d5 b1c3 d5e4 c3e4 c8f5` | 50.0% | 8 |

### Bench (fixed positions, depth 4)

| Position | Nodes | Time (s) | NPS |
|---|---|---|---|
| 1 | 1,495 | 0.076 | 19,739 |
| 2 | 12,722 | 0.475 | 26,782 |
| 3 | 7,727 | 0.252 | 30,652 |
| 4 | 14,491 | 0.574 | 25,252 |
| 5 | 215 | 0.009 | 25,095 |
| 6 | 207 | 0.007 | 27,681 |
| 7 | 4,791 | 0.192 | 24,979 |
| 8 | 6,232 | 0.346 | 18,034 |
| **Total** | **47,880** | **1.930** | **24,807** |

Games: `telemetry/games/elo_v0.2-move-ordering_20261107-233140.pgn`

---

## v0.3-quiescence: Quiescence search

| | |
|---|---|
| **Estimated Elo** | **1147 (95% CI 1098–1195)** |
| Change vs previous version | +63 |
| Games / time control | 200 at 10+0.1 |
| Engine commit | `eec50500bc` |
| Harness commit | `eec50500bc` |
| Recorded | 2026-11-07T23:43:54.222953+00:00 |
| Run duration | 187 s |
| Machine | Intel64 Family 6 Model 141 Stepping 1, GenuineIntel (16 threads), Windows-11-10.0.26200-SP0 |
| Software | Python 3.14.6, chess 1.11.2, Stockfish sf_19 |

### Results

| Split | W | D | L | Games | Score |
|---|---|---|---|---|---|
| Overall | 114 | 43 | 43 | 200 | 67.8% |
| As White | 55 | 23 | 23 | 101 | 65.8% |
| As Black | 59 | 20 | 20 | 99 | 69.7% |
| vs random (217) | 9 | 1 | 0 | 10 | 95.0% |
| vs greedy (697) | 82 | 13 | 0 | 95 | 93.2% |
| vs sf-1320-d1 (1230) | 23 | 29 | 43 | 95 | 39.5% |

### How games ended

| Outcome | Reason | Games |
|---|---|---|
| win | CHECKMATE | 114 |
| draw | THREEFOLD_REPETITION | 43 |
| loss | CHECKMATE | 24 |
| loss | TIME_FORFEIT | 19 |

Game length: avg 59.2 plies (min 19, max 282).

### Search behaviour in games

| Metric | Value |
|---|---|
| Moves searched | 5206 |
| Depth avg / min / max | 3.0 / 3 / 3 |
| Nodes per move avg / max | 3,210 / 66,336 |
| Time per move avg / median / p95 / max | 0.215 / 0.153 / 0.592 / 4.423 s |
| Nodes per second in games | 14,893 |

### Openings

| | Opening line | Score | Games |
|---|---|---|---|
| best | `d2d4 g8f6 c2c4 g7g6 b1c3 d7d5` | 91.7% | 6 |
| best | `e2e4 e7e6 d2d4 d7d5 b1c3 f8b4` | 87.5% | 8 |
| best | `e2e4 e7e5 g1f3 b8c6 b1c3 g8f6 f1b5 f8b4` | 85.7% | 14 |
| worst | `d2d4 d7d5 c2c4 c7c6 g1f3 g8f6 b1c3 d5c4` | 50.0% | 8 |
| worst | `d2d4 g8f6 c2c4 e7e6 b1c3 f8b4` | 50.0% | 8 |
| worst | `d2d4 d7d5 c1f4 g8f6 e2e3 c7c5` | 50.0% | 4 |

### Bench (fixed positions, depth 4)

| Position | Nodes | Time (s) | NPS |
|---|---|---|---|
| 1 | 1,780 | 0.073 | 24,286 |
| 2 | 53,633 | 2.495 | 21,499 |
| 3 | 18,120 | 0.868 | 20,880 |
| 4 | 98,738 | 4.899 | 20,154 |
| 5 | 259 | 0.011 | 24,133 |
| 6 | 233 | 0.014 | 16,358 |
| 7 | 9,477 | 0.537 | 17,637 |
| 8 | 36,119 | 1.499 | 24,090 |
| **Total** | **218,359** | **10.397** | **21,003** |

Games: `telemetry/games/elo_v0.3-quiescence_20261107-234353.pgn`

---

## v0.4-iterative-deepening: Iterative deepening + time management

| | |
|---|---|
| **Estimated Elo** | **1206 (95% CI 1161–1249)** |
| Change vs previous version | +59 |
| Games / time control | 200 at 10+0.1 |
| Engine commit | `c94a1b3070` |
| Harness commit | `c94a1b3070` |
| Recorded | 2026-11-07T23:51:57.977544+00:00 |
| Run duration | 430 s |
| Machine | Intel64 Family 6 Model 141 Stepping 1, GenuineIntel (16 threads), Windows-11-10.0.26200-SP0 |
| Software | Python 3.14.6, chess 1.11.2, Stockfish sf_19 |

### Results

| Split | W | D | L | Games | Score |
|---|---|---|---|---|---|
| Overall | 63 | 55 | 82 | 200 | 45.2% |
| As White | 38 | 24 | 39 | 101 | 49.5% |
| As Black | 25 | 31 | 43 | 99 | 40.9% |
| vs random (217) | 10 | 0 | 0 | 10 | 100.0% |
| vs greedy (697) | 7 | 3 | 0 | 10 | 85.0% |
| vs sf-1320-d1 (1230) | 3 | 4 | 3 | 10 | 50.0% |
| vs sf-1320-d3 (1254) | 23 | 30 | 32 | 85 | 44.7% |
| vs sf-1320 (1320) | 20 | 18 | 47 | 85 | 34.1% |

### How games ended

| Outcome | Reason | Games |
|---|---|---|
| loss | CHECKMATE | 82 |
| win | CHECKMATE | 63 |
| draw | THREEFOLD_REPETITION | 55 |

Game length: avg 78.8 plies (min 18, max 211).

### Search behaviour in games

| Metric | Value |
|---|---|
| Moves searched | 7114 |
| Depth avg / min / max | 2.87 / 1 / 6 |
| Nodes per move avg / max | 2,060 / 8,531 |
| Time per move avg / median / p95 / max | 0.235 / 0.231 / 0.374 / 0.482 s |
| Nodes per second in games | 8,775 |

### Openings

| | Opening line | Score | Games |
|---|---|---|---|
| best | `e2e4 e7e5 g1f3 b8c6 b1c3 g8f6 f1b5 f8b4` | 66.7% | 18 |
| best | `d2d4 g8f6 c2c4 e7e6 b1c3 f8b4` | 62.5% | 4 |
| best | `d2d4 g8f6 c2c4 g7g6 b1c3 d7d5` | 62.5% | 4 |
| worst | `e2e4 c7c5 g1f3 e7e6 d2d4 c5d4 f3d4 a7a6` | 12.5% | 8 |
| worst | `e2e4 e7e6 d2d4 d7d5 b1c3 f8b4` | 18.8% | 8 |
| worst | `e2e4 c7c6 d2d4 d7d5 b1c3 d5e4 c3e4 c8f5` | 25.0% | 8 |

### Bench (fixed positions, depth 4)

| Position | Nodes | Time (s) | NPS |
|---|---|---|---|
| 1 | 2,401 | 0.097 | 24,687 |
| 2 | 54,940 | 2.162 | 25,417 |
| 3 | 17,158 | 0.559 | 30,701 |
| 4 | 111,964 | 4.500 | 24,882 |
| 5 | 401 | 0.020 | 19,773 |
| 6 | 357 | 0.018 | 19,520 |
| 7 | 11,625 | 0.554 | 20,998 |
| 8 | 49,207 | 1.897 | 25,938 |
| **Total** | **248,053** | **9.807** | **25,294** |

Games: `telemetry/games/elo_v0.4-iterative-deepening_20261107-235157.pgn`

---

## v0.5-transposition-table: Transposition table

| | |
|---|---|
| **Estimated Elo** | **1171 (95% CI 1125–1222)** |
| Change vs previous version | -35 |
| Games / time control | 200 at 10+0.1 |
| Engine commit | `e2f5147fa3` |
| Harness commit | `e2f5147fa3` |
| Recorded | 2026-11-07T23:57:16.799242+00:00 |
| Run duration | 222 s |
| Machine | Intel64 Family 6 Model 141 Stepping 1, GenuineIntel (16 threads), Windows-11-10.0.26200-SP0 |
| Software | Python 3.14.6, chess 1.11.2, Stockfish sf_19 |

### Results

| Split | W | D | L | Games | Score |
|---|---|---|---|---|---|
| Overall | 109 | 61 | 30 | 200 | 69.8% |
| As White | 59 | 24 | 18 | 101 | 70.3% |
| As Black | 50 | 37 | 12 | 99 | 69.2% |
| vs random (217) | 10 | 0 | 0 | 10 | 100.0% |
| vs greedy (697) | 75 | 20 | 0 | 95 | 89.5% |
| vs sf-1320-d1 (1230) | 24 | 41 | 30 | 95 | 46.8% |

### How games ended

| Outcome | Reason | Games |
|---|---|---|
| win | CHECKMATE | 109 |
| draw | THREEFOLD_REPETITION | 61 |
| loss | CHECKMATE | 30 |

Game length: avg 65.1 plies (min 19, max 164).

### Search behaviour in games

| Metric | Value |
|---|---|
| Moves searched | 5782 |
| Depth avg / min / max | 2.92 / 1 / 5 |
| Nodes per move avg / max | 2,172 / 8,584 |
| Time per move avg / median / p95 / max | 0.246 / 0.245 / 0.382 / 0.535 s |
| Nodes per second in games | 8,842 |

### Openings

| | Opening line | Score | Games |
|---|---|---|---|
| best | `d2d4 d7d5 c1f4 g8f6 e2e3 c7c5` | 87.5% | 4 |
| best | `e2e4 e7e5 g1f3 b8c6 b1c3 g8f6 f1b5 f8b4` | 82.1% | 14 |
| best | `e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6` | 81.2% | 8 |
| worst | `e2e4 d7d6 d2d4 g8f6 b1c3 g7g6` | 25.0% | 4 |
| worst | `e2e4 e7e5 b1c3 g8f6 f2f4 d7d5` | 50.0% | 4 |
| worst | `d2d4 g8f6 c2c4 g7g6 b1c3 d7d5` | 58.3% | 6 |

### Bench (fixed positions, depth 4)

| Position | Nodes | Time (s) | NPS |
|---|---|---|---|
| 1 | 2,046 | 0.077 | 26,607 |
| 2 | 34,040 | 1.155 | 29,474 |
| 3 | 8,403 | 0.298 | 28,157 |
| 4 | 73,908 | 2.815 | 26,255 |
| 5 | 388 | 0.022 | 17,924 |
| 6 | 339 | 0.019 | 18,253 |
| 7 | 8,431 | 0.393 | 21,427 |
| 8 | 40,000 | 1.388 | 28,824 |
| **Total** | **167,555** | **6.167** | **27,171** |

Games: `telemetry/games/elo_v0.5-transposition-table_20261107-235716.pgn`

---
