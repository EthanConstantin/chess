# Benchmarking, Telemetry and Elo Estimation

The `harness/` package measures every engine version the same way, so a change in a
number reflects a change in the engine and nothing else. **Estimated Elo is the headline
metric.** Everything else explains *why* Elo moved.

## Versions

- Each feature lands as a git tag: `v0.1-baseline`, `v0.2-move-ordering`,
  `v0.3-quiescence`, …
- The harness checks out any tag into a temporary `git worktree` and runs it as a UCI
  subprocess. Old versions can be re-measured at any time, and two versions can be
  matched against each other.

```
python -m harness run    --version v0.3-quiescence   # bench + tactics + Elo
python -m harness match  v0.3-quiescence v0.2-move-ordering
python -m harness report                             # charts + README table
```

## What is recorded

Each run appends one JSON record to `telemetry/results.jsonl`, which is committed to the
repo:

| Group | Metrics |
|---|---|
| Identity | version tag, git SHA, feature label, timestamp |
| Environment | CPU, OS, Python version, `python-chess` version, Stockfish version |
| Bench (fixed position set, fixed depth) | total nodes, time, nodes/sec, effective branching factor, time to depth *N*, TT hit rate (once a TT exists) |
| Tactics | solve rate on the Win At Chess (WAC) suite at a fixed time per position |
| **Elo** | **estimate, 95% confidence interval**, games played, W/D/L per opponent |
| Head-to-head | Elo difference vs the previous version, with an SPRT result where used |

`python -m harness report` turns this file into:
- an **Elo-by-version chart** (the README headline image)
- a per-feature table: feature, Elo gain ± error, node reduction, NPS change
- the README headline numbers (generated, never typed in by hand)

## How Elo is estimated

Elo is relative: it only means something against a fixed, rated pool of opponents. The
harness plays the engine against **anchor engines with known ratings** and fits a single
rating by maximum likelihood across all their games.

### Anchors
| Anchor | Rating source |
|---|---|
| Stockfish with `UCI_LimitStrength=true`, `UCI_Elo` = 1320, 1500, 1700, 2000, … | Stockfish's own calibration (CCRL-like scale). 1320 is the lowest setting Stockfish allows. |
| Low-end anchors: random mover, greedy 1-ply material engine | Rated once by playing them against the Stockfish anchors. The ratings are then frozen. |

Low-end anchors are needed because the early versions will lose almost every game to
Stockfish at 1320. A 0% or 100% score gives no usable Elo, so opponents are chosen from
the anchor list so that each match scores roughly between 20% and 80%.

### Match protocol (fixed for every run)
- Time control: one fixed time control (e.g. 10s + 0.1s per game). It must stay the
  same across all versions.
- Openings: a fixed set of balanced openings. Each opening is played twice with colors
  swapped, to cancel opening bias.
- Games: at least ~200 games per measured version. More games give tighter error bars;
  the confidence interval is always reported next to the estimate.
- Matches run in parallel and are driven through UCI with `chess.engine`.
- Same machine, same Stockfish build, and same opening set for every version. If any of
  these change, every version is re-run.

### Being honest about the number
- The estimate is on a **CCRL-like engine scale under the stated time control**. It is
  not a chess.com or lichess rating for human players, and the README says so.
- Ratings below ~1320 are extrapolated through the low-end anchors and have wider error
  bars.
- Each Elo figure is shown with its ± interval. A gain smaller than its error bar is
  reported as "no significant change".

## Current setup (as implemented)

```
python -m harness setup                       # download pinned Stockfish (sf_19) into tools/
python -m harness calibrate --games 100       # rate the sub-1320 anchors -> telemetry/anchors.json
python -m harness run --version <tag> --label "<feature>"   # bench + Elo -> telemetry/results.jsonl
python -m harness report                      # README table
```

- Time control: **10+0.1**, 24 opening lines each played with both colors, max 400 plies.
- Elo: probe 10 games per ladder rung until the engine scores under 50%, then split the
  remaining games between the two rungs that bracket it (200 games total).
- Anchor ladder (calibrated 2026-11-02, 100 games per adjacent pair):

  | Anchor | Rating | 95% CI |
  |---|---|---|
  | random mover | 217 | 7–349 |
  | greedy (1-ply material) | 697 | 531–819 |
  | Stockfish UCI_Elo 1320, depth 1 | 1230 | 1135–1319 |
  | Stockfish UCI_Elo 1320, depth 3 | 1254 | 1183–1320 |
  | Stockfish UCI_Elo 1320 / 1500 / 1700 / 1900 / 2100 / 2400 | fixed | n/a |

### Known limitations
- The engine's ± interval covers game noise only, not the uncertainty in the calibrated
  anchors. Below 1320, add roughly ±90 for anchor uncertainty.
- Stockfish calibrates `UCI_Elo` at 60+0.6. The harness uses 10+0.1 for throughput, so
  the absolute scale is approximate. Comparisons *between versions* are unaffected,
  because every version uses the same conditions.
- The two depth-limited rungs (d1 and d3) came out almost equal in strength, and greedy
  scored 0 wins, 8 draws and 92 losses against d1. A rung between them (e.g. Stockfish at a
  small node limit) would tighten the 700–1200 range.
- Run benchmarks on an otherwise idle machine. The same bench measured 19.8k nps while
  calibration games were running and 32.9k nps on an idle machine.
- The tactics suite (WAC) is not implemented yet.

## Speed note
Elo is measured on a local machine. The live site runs the same code on Vercel's
serverless CPUs, which are slower, so it plays weaker at the same time per move. The
site's difficulty selector is labeled by time per move, not by Elo.
