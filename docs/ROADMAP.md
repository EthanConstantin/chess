# Roadmap

Guiding principle: **few features, each done properly and measured.** Every feature lands
as its own tagged version (`v0.1`, `v0.2`, …) and is run through the benchmark harness
before the next one starts. The README headline comes straight from that data.

## Architecture decisions

### 1. Move generation: use `python-chess`
Writing a move generator or bitboards adds a lot of work for little portfolio value. The
engine's own work is search and evaluation. `python-chess` is pure Python, so it also runs
in the browser.

### 2. Web: Flask API as a Vercel serverless function
The goal is for the engine to be playable **inside the portfolio site** without sending
visitors anywhere else, on free hosting with fast startup.

| Option | Free | Cold start | Notes |
|---|---|---|---|
| **Flask on Vercel (Python serverless function)** | **Yes (hobby tier, no card)** | **About a second** | **Chosen.** Vercel also hosts the board page. |
| Flask on Render / Railway / HF Spaces (always-on server) | Yes | 30–60s after sleeping | Visitors would hit a sleeping server. |
| Google Cloud Run / AWS Lambda | Free tier | Fast | Need a billing card. Lambda setup is fiddlier. |
| Pyodide (Python in the browser) | Yes | None | Engine runs slower in the browser and needs a ~10 MB first download. Rejected. |

**Decision:** Flask, deployed to Vercel as a serverless function.
- **Stateless API:** `POST /api/move {fen, movetime_ms}` returns
  `{move, score, depth, nodes, pv}`. Every request carries the full position, so any fresh
  function instance can answer it.
- **Time cap:** about 1–3 seconds per move, which keeps requests well inside Vercel's
  function time limit. Iterative deepening (Phase 2) makes the engine stop on time.
- **Front end:** a static page (board via `cm-chessboard`, MIT-licensed) served by Vercel.
  The portfolio site embeds it, or calls the API directly with CORS allowed for the
  portfolio's domain.
- **Strength note:** serverless CPUs are modest, so the live site plays somewhat weaker
  than the Elo measured locally. Elo is always measured on a local machine under fixed
  conditions. See [BENCHMARKING.md](BENCHMARKING.md).

### 3. UCI protocol
The engine speaks UCI so the harness can play rated matches against reference engines.
It also allows a lichess bot later.

## Phases

### Phase 0: Measurement first
Build the harness **before** improving the engine, so that the baseline is recorded.
- `harness/` package: bench, tactics suite, Elo matches, results store, report.
  Full details are in [BENCHMARKING.md](BENCHMARKING.md).
- Tag the current engine (with only its bugs fixed, see Phase 1) as **`v0.1-baseline`**
  and record its Elo. This is the "from" number in the headline.

### Phase 1: Correct core
- Fix the alpha-beta window: the recursive call must pass `(-beta, -alpha)`. Currently it
  passes `(-alpha, -beta)`, which prunes everything after the first move at every non-root
  node.
- Score from the perspective of the side to move (negamax requirement).
- Score checkmate as a large value adjusted by ply (prefer faster mates). Score stalemate
  and other draws as 0.
- Use centipawns (pawn = 100) and integer scores.
- Restructure into the `engine/` package. Add a `Searcher` class and remove module-level
  globals.
- Add a UCI loop (`engine/uci.py`).
- Tests: alpha-beta returns the same score as plain minimax, mate-in-1 and mate-in-2,
  stalemate, "take the free queen", and a UCI smoke test.
- Clean up `requirements.txt` (`chess` instead of the `python-chess` shim, add pytest).

### Phase 2: Search (each step is a tagged, measured version)
1. Move ordering: captures by MVV-LVA, then quiet moves.
2. Quiescence search: captures only at leaf nodes, which removes horizon blunders.
3. Iterative deepening with a time limit, searching the previous best move first.
4. Transposition table using `chess.polyglot.zobrist_hash`.
5. *(Optional)* Killer moves and history heuristic, null-move pruning.

**Status (steps 1–4 done, measured 2026-11-07, 200 games each at 10+0.1):**

| Version | Elo | Bench nodes (d4) | Notes |
|---|---|---|---|
| v0.1-baseline | 1075 ± 50 | 362,643 | 4 time forfeits |
| v0.2-move-ordering | 1084 ± 46 | 47,880 | 7.6× fewer nodes; still fixed depth 3, so no Elo change expected |
| v0.3-quiescence | 1147 ± 49 | 218,359 | Checkmate losses 44 → 24, but 19 time forfeits (fixed depth, no clock) |
| v0.4-iterative-deepening | 1206 ± 44 | 248,053 | Zero time forfeits; longest move 0.48 s |
| v0.5-transposition-table | 1171 ± 49 | 167,555 | Within error of v0.4: no significant change |

Findings:
- Elo comes from v0.3 and v0.4 (+131 combined, outside the error bars). Ordering and the TT
  are speed features: they cut nodes (7.6× and 1.5×), which matters once deeper searches
  fit in the budget.
- In-game NPS is about 9k (8 parallel games), against 27k in the idle bench, so the
  engine reaches only depth ~3 per move. Search improvements are capped by Python speed
  and the material-only evaluation.
- Head-to-head v0.4 vs v0.5: 198 of 200 games were threefold repetitions (median 19
  plies). With material-only evaluation every quiet move scores 0, so two versions of the
  engine shuffle pieces until a repetition. Self-play cannot rank versions until Phase 3
  adds positional terms. Use the anchor ladder until then.
- The TT is keyed by python-chess's private `Board._transposition_key()`, not
  `chess.polyglot.zobrist_hash` as first planned: zobrist_hash measured ~45 µs per call
  against ~2 µs, which would have halved NPS.

### Phase 3: Evaluation
1. Piece-square tables, with a tapered king table for middlegame and endgame.
2. Pawn structure: passed, doubled and isolated pawns. A term is kept only if it gains
   measurable Elo.

### Phase 4: Web
- `api/`: Flask app exposing `POST /api/move` as a Vercel serverless function, plus a
  `vercel.json` config.
- `web/`: static board page with an info panel showing eval, depth, nodes and the
  principal variation.
- Difficulty selector based on time per move (capped at about 3 seconds).
- CORS restricted to the portfolio's domain.
- Deploy to Vercel and embed in the portfolio.

### Phase 5: Presentation
- README: headline Elo, Elo-by-version chart, per-feature table, gameplay GIF, and a
  short "how it works" section.
- GitHub Actions: pytest plus a quick bench smoke test, with a status badge.

## Out of scope
Custom move generation or bitboards, neural-network evaluation, large opening books,
endgame tablebases.
