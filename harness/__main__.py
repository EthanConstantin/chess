"""Command-line interface for the measurement and benchmarking harness.

Provides subcommands to calibrate reference anchors, run position benchmarks,
estimate Elo ratings, play head-to-head matches, and compile telemetry reports.
"""

import argparse
import os
from pathlib import Path
import re
import sys

from harness.bench import run_bench
from harness.calibrate import calibrate
from harness.elo import estimate_elo
from harness.match import TimeControl, play_match
from harness.rating import bootstrap_interval, fit_ratings
from harness.stockfish import install_stockfish
from harness.telemetry import (
    append_record,
    environment,
    load_records,
    save_pgn,
)
from harness.versions import resolve_version

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONCURRENCY = max(1, (os.cpu_count() or 2) // 2)
DEFAULT_TC = "10+0.1"

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def cmd_setup(_args: argparse.Namespace) -> None:
    """Download and configure pinned Stockfish."""
    install_stockfish()


def cmd_calibrate(args: argparse.Namespace) -> None:
    """Calibrate anchor ratings."""
    calibrate(games_per_pair=args.games, tc=args.tc, concurrency=args.concurrency)


def cmd_bench(args: argparse.Namespace) -> None:
    """Run bench position suite."""
    spec = resolve_version(args.version)
    report = run_bench(spec, depth=args.depth)
    print(f"\nBench report for {args.version} (depth {report['depth']}):")
    print(f"{'Position':<10} {'Nodes':>10} {'Time (s)':>10} {'NPS':>12}")
    print("-" * 46)
    for i, p in enumerate(report["positions"]):
        print(f"Pos {i + 1:<6} {p['nodes']:>10} {p['time_s']:>10.3f} {p['nps']:>12,.0f}")
    print("-" * 46)
    print(
        f"{'Total':<10} {report['nodes']:>10} {report['time_s']:>10.3f} {report['nps']:>12,.0f}\n"
    )


def cmd_elo(args: argparse.Namespace) -> None:
    """Estimate Elo against anchor ladder."""
    spec = resolve_version(args.version)
    res = estimate_elo(
        spec,
        games=args.games,
        tc=args.tc,
        concurrency=args.concurrency,
    )
    print(f"\nEstimated Elo for {args.version}: {res['rating']:.1f}")
    print(f"95% CI: [{res['ci_lo']:.1f}, {res['ci_hi']:.1f}] ({res['games']} games, tc {res['tc']})")
    print("\nOpponents breakdown:")
    for opp, info in res["opponents"].items():
        print(
            f"  {opp:<15} (rating {info['rating']:.0f}): +{info['w']} ={info['d']} -{info['l']}"
        )


def cmd_run(args: argparse.Namespace) -> None:
    """Run bench and Elo estimation, recording results to telemetry."""
    spec = resolve_version(args.version)
    print(f"Running bench for {args.version}...")
    bench_data = run_bench(spec, depth=args.depth)

    print(f"\nRunning Elo estimation for {args.version}...")
    elo_data = estimate_elo(
        spec,
        games=args.games,
        tc=args.tc,
        concurrency=args.concurrency,
    )

    record = {
        "version": args.version,
        "label": args.label,
        "sha": spec.sha,
        "env": environment(),
        "bench": bench_data,
        "elo": elo_data,
    }
    append_record(record)
    print(f"\nRecorded result for {args.version} ({args.label}):")
    err = (elo_data["ci_hi"] - elo_data["ci_lo"]) / 2.0
    print(
        f"Elo {elo_data['rating']:.0f} ± {err:.0f} | Bench Nodes: {bench_data['nodes']} | NPS: {bench_data['nps']:,.0f}"
    )


def cmd_match(args: argparse.Namespace) -> None:
    """Head-to-head match between two engine versions."""
    spec_a = resolve_version(args.A)
    spec_b = resolve_version(args.B)
    tc = TimeControl.parse(args.tc)

    print(f"Starting match: {spec_a.name} vs {spec_b.name} ({args.games} games, tc {tc})...")
    games_res = play_match(
        spec_a,
        spec_b,
        games=args.games,
        tc=tc,
        concurrency=args.concurrency,
    )

    w = sum(
        1
        for g in games_res
        if (g.white == spec_a.name and g.white_score == 1.0)
        or (g.black == spec_a.name and g.white_score == 0.0)
    )
    d = sum(1 for g in games_res if g.white_score == 0.5)
    l = sum(
        1
        for g in games_res
        if (g.white == spec_a.name and g.white_score == 0.0)
        or (g.black == spec_a.name and g.white_score == 1.0)
    )
    score = w + 0.5 * d

    rating_games = [(g.white, g.black, g.white_score) for g in games_res]
    fixed = {spec_a.name: 0.0}
    fitted = fit_ratings(rating_games, fixed=fixed)
    diff = fitted[spec_b.name]
    ci_lo, ci_hi = bootstrap_interval(rating_games, fixed=fixed, player=spec_b.name)

    print(f"\nResult: {spec_a.name} vs {spec_b.name}: +{w} ={d} -{l} ({score}/{args.games})")
    print(f"Elo difference ({spec_b.name} - {spec_a.name}): {diff:+.1f} [95% CI: {ci_lo:+.1f}, {ci_hi:+.1f}]")
    save_pgn(games_res, f"match_{spec_a.name}_vs_{spec_b.name}")


def cmd_report(_args: argparse.Namespace) -> None:
    """Generate telemetry markdown table and update README.md."""
    records = load_records()
    table_lines = [
        "| Version | Feature | Elo | Games | Bench Nodes | NPS | Δ Elo |",
        "|---|---|---|---|---|---|---|",
    ]

    prev_rating: float | None = None
    for r in records:
        v = r.get("version", "-")
        lbl = r.get("label", "-")
        elo_obj = r.get("elo", {})
        rating = elo_obj.get("rating")
        ci_lo = elo_obj.get("ci_lo")
        ci_hi = elo_obj.get("ci_hi")

        if rating is not None and ci_lo is not None and ci_hi is not None:
            err = (ci_hi - ci_lo) / 2.0
            elo_str = f"{rating:.0f} ± {err:.0f}"
        else:
            elo_str = "-"

        games_str = str(elo_obj.get("games", "-"))

        bench_obj = r.get("bench", {})
        nodes = bench_obj.get("nodes")
        nodes_str = f"{nodes:,}" if isinstance(nodes, (int, float)) else "-"

        nps = bench_obj.get("nps")
        nps_str = f"{nps:,.0f}" if isinstance(nps, (int, float)) else "-"

        if prev_rating is not None and rating is not None:
            diff = rating - prev_rating
            delta_str = f"{diff:+.0f}"
        else:
            delta_str = "-"

        if rating is not None:
            prev_rating = rating

        table_lines.append(
            f"| {v} | {lbl} | {elo_str} | {games_str} | {nodes_str} | {nps_str} | {delta_str} |"
        )

    table_text = "\n".join(table_lines)
    print(table_text)

    readme_path = ROOT / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        pattern = r"(<!-- ELO_TABLE:START.*?-->\n)(?:[\s\S]*?\n)?(<!-- ELO_TABLE:END -->)"
        replacement = rf"\g<1>{table_text}\n\g<2>"
        new_content = re.sub(pattern, replacement, content)
        readme_path.write_text(new_content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m harness",
        description="Measurement and benchmarking harness for chess engine development.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # setup
    p_setup = subparsers.add_parser("setup", help="Install pinned Stockfish build")
    p_setup.set_defaults(func=cmd_setup)

    # calibrate
    p_cal = subparsers.add_parser("calibrate", help="Calibrate low-end anchor ratings")
    p_cal.add_argument("--games", type=int, default=40, help="Games per anchor pair (default: 40)")
    p_cal.add_argument("--tc", type=str, default=DEFAULT_TC, help=f"Time control (default: {DEFAULT_TC})")
    p_cal.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Worker concurrency (default: {DEFAULT_CONCURRENCY})",
    )
    p_cal.set_defaults(func=cmd_calibrate)

    # bench
    p_bench = subparsers.add_parser("bench", help="Run benchmark suite on an engine version")
    p_bench.add_argument("--version", type=str, required=True, help="Engine version/git ref")
    p_bench.add_argument("--depth", type=int, default=4, help="Search depth (default: 4)")
    p_bench.set_defaults(func=cmd_bench)

    # elo
    p_elo = subparsers.add_parser("elo", help="Estimate Elo against anchor ladder")
    p_elo.add_argument("--version", type=str, required=True, help="Engine version/git ref")
    p_elo.add_argument("--games", type=int, default=200, help="Total games (default: 200)")
    p_elo.add_argument("--tc", type=str, default=DEFAULT_TC, help=f"Time control (default: {DEFAULT_TC})")
    p_elo.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Worker concurrency (default: {DEFAULT_CONCURRENCY})",
    )
    p_elo.set_defaults(func=cmd_elo)

    # run
    p_run = subparsers.add_parser("run", help="Run bench + Elo estimation and record telemetry")
    p_run.add_argument("--version", type=str, required=True, help="Engine version/git ref")
    p_run.add_argument("--label", type=str, required=True, help="Feature label description")
    p_run.add_argument("--games", type=int, default=200, help="Total games (default: 200)")
    p_run.add_argument("--depth", type=int, default=4, help="Bench search depth (default: 4)")
    p_run.add_argument("--tc", type=str, default=DEFAULT_TC, help=f"Time control (default: {DEFAULT_TC})")
    p_run.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Worker concurrency (default: {DEFAULT_CONCURRENCY})",
    )
    p_run.set_defaults(func=cmd_run)

    # match
    p_match = subparsers.add_parser("match", help="Head-to-head match between two engine versions")
    p_match.add_argument("A", type=str, help="First engine ref")
    p_match.add_argument("B", type=str, help="Second engine ref")
    p_match.add_argument("--games", type=int, default=100, help="Total games (default: 100)")
    p_match.add_argument("--tc", type=str, default=DEFAULT_TC, help=f"Time control (default: {DEFAULT_TC})")
    p_match.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Worker concurrency (default: {DEFAULT_CONCURRENCY})",
    )
    p_match.set_defaults(func=cmd_match)

    # report
    p_report = subparsers.add_parser("report", help="Generate summary report and update README.md")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
