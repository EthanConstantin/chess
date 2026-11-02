# AGENTS.md

Shared rules for any AI agent (Claude, Antigravity/Gemini) working in this repo.

## Project
A Python chess engine built as a student portfolio piece. Read `docs/ROADMAP.md` and
`docs/BENCHMARKING.md` before starting work.

## Stack
- Python 3.12+ (developed on 3.14). Virtual env: `.venv/`.
- Move generation and board representation: the `chess` package (python-chess). Do not
  write a custom move generator.
- Tests: pytest. Run with `.venv/Scripts/python -m pytest -q` (Windows) or
  `.venv/bin/python -m pytest -q`.
- Web (later phase): Flask, deployed as a Vercel serverless function.

## Conventions
- Scores are integers in centipawns (pawn = 100).
- Search scores are always from the perspective of the side to move (negamax).
- No module-level mutable state in the engine (no globals for node counts etc.).
- Keep code small and readable. This is a portfolio piece: clarity beats cleverness.
  Short docstrings on public functions; explain *why*, not *what*.
- No new dependencies without a stated reason.

## Hard rules
- Never edit tests under `tests/` to make them pass. If a test looks wrong, say so.
- Never modify installed packages or stub out dependencies.
- Do not commit; leave changes uncommitted for review.
