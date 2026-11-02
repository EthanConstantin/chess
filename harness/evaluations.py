"""Render telemetry/results.jsonl into EVALUATIONS.md: one detailed section per version."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALUATIONS_PATH = ROOT / "EVALUATIONS.md"


def _fmt(value, spec: str = "", default: str = "-") -> str:
    if value is None:
        return default
    return format(value, spec)


def _elo_str(elo: dict) -> str:
    if elo.get("rating") is None:
        return "-"
    return f"{elo['rating']:.0f} (95% CI {elo['ci_lo']:.0f}–{elo['ci_hi']:.0f})"


def _wdl_row(name: str, wdl: dict) -> str:
    return (f"| {name} | {wdl['w']} | {wdl['d']} | {wdl['l']} | {wdl['games']} "
            f"| {_fmt(wdl.get('score_pct'), '.1f')}% |")


def render_version(record: dict, previous: dict | None) -> str:
    elo = record.get("elo", {})
    bench = record.get("bench", {})
    stats = elo.get("stats", {})
    env = record.get("env", {})
    run = record.get("run", {})
    lines = [f"## {record.get('version')}: {record.get('label', '')}", ""]

    delta = "-"
    if previous and previous.get("elo", {}).get("rating") is not None and elo.get("rating") is not None:
        delta = f"{elo['rating'] - previous['elo']['rating']:+.0f}"
    lines += [
        "| | |",
        "|---|---|",
        f"| **Estimated Elo** | **{_elo_str(elo)}** |",
        f"| Change vs previous version | {delta} |",
        f"| Games / time control | {elo.get('games', '-')} at {elo.get('tc', '-')} |",
        f"| Engine commit | `{(record.get('sha') or 'working tree')[:10]}` |",
        f"| Harness commit | `{(run.get('harness_sha') or '-')[:10]}`{' (dirty)' if run.get('harness_dirty') else ''} |",
        f"| Recorded | {record.get('timestamp', '-')} |",
        f"| Run duration | {_fmt(run.get('duration_s'), '.0f')} s |",
        f"| Machine | {env.get('cpu', '-')} ({env.get('cpu_count', '-')} threads), {env.get('platform', '-')} |",
        f"| Software | Python {env.get('python', '-')}, chess {env.get('chess', '-')}, Stockfish {env.get('stockfish', '-')} |",
        "",
    ]

    if stats:
        lines += ["### Results", "", "| Split | W | D | L | Games | Score |", "|---|---|---|---|---|---|"]
        lines.append(_wdl_row("Overall", stats["overall"]))
        lines.append(_wdl_row("As White", stats["as_white"]))
        lines.append(_wdl_row("As Black", stats["as_black"]))
        for opp, wdl in stats["by_opponent"].items():
            rating = elo.get("opponents", {}).get(opp, {}).get("rating")
            lines.append(_wdl_row(f"vs {opp} ({_fmt(rating, '.0f')})", wdl))
        lines.append("")

        lines += ["### How games ended", "", "| Outcome | Reason | Games |", "|---|---|---|"]
        for key, count in stats["endings"].items():
            outcome, reason = key.split(":", 1)
            lines.append(f"| {outcome} | {reason} | {count} |")
        gl = stats["game_length_plies"]
        lines += ["", f"Game length: avg {gl['avg']} plies (min {gl['min']}, max {gl['max']}).", ""]

        s = stats["search"]
        lines += [
            "### Search behaviour in games", "",
            "| Metric | Value |", "|---|---|",
            f"| Moves searched | {s.get('moves', 0)} |",
            f"| Depth avg / min / max | {_fmt(s.get('depth_avg'))} / {_fmt(s.get('depth_min'))} / {_fmt(s.get('depth_max'))} |",
            f"| Nodes per move avg / max | {_fmt(s.get('nodes_avg'), ',')} / {_fmt(s.get('nodes_max'), ',')} |",
            f"| Time per move avg / median / p95 / max | {_fmt(s.get('time_avg_s'), '.3f')} / {_fmt(s.get('time_median_s'), '.3f')} / {_fmt(s.get('time_p95_s'), '.3f')} / {_fmt(s.get('time_max_s'), '.3f')} s |",
            f"| Nodes per second in games | {_fmt(s.get('nps_in_games'), ',')} |",
            "",
        ]

        worst = sorted(stats["by_opening"].items(), key=lambda kv: kv[1]["score_pct"])[:3]
        best = sorted(stats["by_opening"].items(), key=lambda kv: -kv[1]["score_pct"])[:3]
        lines += ["### Openings", "", "| | Opening line | Score | Games |", "|---|---|---|---|"]
        for tag, group in (("best", best), ("worst", worst)):
            for line, wdl in group:
                lines.append(f"| {tag} | `{line}` | {wdl['score_pct']}% | {wdl['games']} |")
        lines.append("")

    if bench:
        lines += [
            f"### Bench (fixed positions, depth {bench.get('depth')})", "",
            "| Position | Nodes | Time (s) | NPS |", "|---|---|---|---|",
        ]
        for i, p in enumerate(bench.get("positions", []), 1):
            lines.append(f"| {i} | {p['nodes']:,} | {p['time_s']:.3f} | {p['nps']:,.0f} |")
        lines.append(f"| **Total** | **{bench['nodes']:,}** | **{bench['time_s']:.3f}** | **{bench['nps']:,.0f}** |")
        lines.append("")

    if elo.get("pgn_path"):
        pgn = Path(elo["pgn_path"])
        try:
            pgn = pgn.resolve().relative_to(ROOT)
        except ValueError:
            pass
        lines += [f"Games: `{pgn.as_posix()}`", ""]
    return "\n".join(lines)


def render(records: list[dict]) -> str:
    out = [
        "# Evaluations",
        "",
        "Every engine version measured by the harness, newest last. Generated from",
        "`telemetry/results.jsonl` by `python -m harness report`; do not edit by hand.",
        "Methodology and caveats: [docs/BENCHMARKING.md](docs/BENCHMARKING.md).",
        "",
        "| Version | Feature | Elo | Δ | Games |",
        "|---|---|---|---|---|",
    ]
    prev = None
    for r in records:
        elo = r.get("elo", {})
        d = "-"
        if prev and prev.get("elo", {}).get("rating") is not None and elo.get("rating") is not None:
            d = f"{elo['rating'] - prev['elo']['rating']:+.0f}"
        rating = _fmt(elo.get("rating"), ".0f")
        err = ""
        if elo.get("ci_lo") is not None:
            err = f" ± {(elo['ci_hi'] - elo['ci_lo']) / 2:.0f}"
        out.append(f"| [{r.get('version')}](#{_anchor(r)}) | {r.get('label', '')} | {rating}{err} | {d} | {elo.get('games', '-')} |")
        prev = r
    out.append("")
    prev = None
    for r in records:
        out += [render_version(r, prev), "---", ""]
        prev = r
    return "\n".join(out)


def _anchor(record: dict) -> str:
    heading = f"{record.get('version')}: {record.get('label', '')}".lower()
    return "".join(c for c in heading.replace(" ", "-") if c.isalnum() or c in "-_")


def write_evaluations(records: list[dict], path: Path = EVALUATIONS_PATH) -> Path:
    path.write_text(render(records), encoding="utf-8")
    return path
