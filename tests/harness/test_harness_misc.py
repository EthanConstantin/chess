import json
import subprocess
import sys
from pathlib import Path

import chess
import chess.engine
import pytest

from harness.bench import BENCH_POSITIONS, run_bench
from harness.stockfish import find_stockfish
from harness.telemetry import append_record, environment, load_records
from harness.versions import ANCHOR_LADDER, anchor_spec, resolve_version

ROOT = Path(__file__).resolve().parents[2]


def test_players_greedy_takes_free_queen():
    spec = anchor_spec("greedy")
    with chess.engine.SimpleEngine.popen_uci(spec.command, cwd=spec.cwd) as engine:
        board = chess.Board("4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1")
        result = engine.play(board, chess.engine.Limit(time=1))
        assert result.move == chess.Move.from_uci("d1d5")


def test_players_random_plays_legal_moves():
    spec = anchor_spec("random")
    with chess.engine.SimpleEngine.popen_uci(spec.command, cwd=spec.cwd) as engine:
        board = chess.Board()
        for _ in range(10):
            move = engine.play(board, chess.engine.Limit(time=1)).move
            assert move in board.legal_moves
            board.push(move)


def test_anchor_ladder_is_ordered_and_has_fixed_stockfish_anchors():
    names = [a.name for a in ANCHOR_LADDER]
    assert names[0] == "random" and names[1] == "greedy"
    fixed = [a for a in ANCHOR_LADDER if a.fixed_rating is not None]
    assert [a.fixed_rating for a in fixed] == sorted(a.fixed_rating for a in fixed)
    assert fixed and fixed[0].fixed_rating == 1320
    for a in fixed:
        assert a.name == f"sf-{a.fixed_rating}"


@pytest.mark.skipif(find_stockfish() is None, reason="Stockfish not installed (python -m harness setup)")
def test_stockfish_anchor_spec_limits_strength():
    spec = anchor_spec("sf-1500")
    assert spec.options["UCI_LimitStrength"] is True
    assert spec.options["UCI_Elo"] == 1500
    assert spec.options["Threads"] == 1


def test_resolve_working_tree():
    spec = resolve_version("working")
    assert Path(spec.cwd).resolve() == ROOT
    assert spec.command[-2:] == ["-m", "engine.uci"]


def test_resolve_git_ref_uses_worktree():
    spec = resolve_version("HEAD")
    cwd = Path(spec.cwd)
    assert cwd != ROOT
    assert (cwd / "engine" / "uci.py").exists()
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout.strip()
    assert spec.sha == sha
    # Resolving again reuses the same worktree.
    assert resolve_version("HEAD").cwd == spec.cwd


def test_bench_reports_nodes_and_speed():
    report = run_bench(resolve_version("working"), depth=2)
    assert len(report["positions"]) == len(BENCH_POSITIONS)
    assert report["depth"] == 2
    assert report["nodes"] == sum(p["nodes"] for p in report["positions"])
    assert report["nodes"] > 0 and report["time_s"] > 0 and report["nps"] > 0


def test_telemetry_roundtrip(tmp_path):
    path = tmp_path / "results.jsonl"
    append_record({"version": "v0", "elo": 1000}, path=path)
    append_record({"version": "v1", "elo": 1100}, path=path)
    records = load_records(path=path)
    assert [r["version"] for r in records] == ["v0", "v1"]
    assert all("timestamp" in r for r in records)
    lines = path.read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["elo"] == 1000


def test_environment_info():
    env = environment()
    for key in ("python", "chess", "platform", "cpu_count", "stockfish"):
        assert key in env


def test_cli_help():
    proc = subprocess.run([sys.executable, "-m", "harness", "--help"], cwd=ROOT,
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0
    for cmd in ("setup", "calibrate", "bench", "elo", "run", "match", "report"):
        assert cmd in proc.stdout
