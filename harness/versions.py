"""Engine specification, anchor ladders, and git worktree resolution.

Every engine version is run as an isolated UCI subprocess, either from the
working tree or from a detached git worktree for historic tags.
"""

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import sys

from harness.stockfish import find_stockfish

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class EngineSpec:
    name: str
    command: list[str]
    cwd: str
    options: dict = field(default_factory=dict)
    limit: dict | None = None
    sha: str | None = None


@dataclass
class Anchor:
    name: str
    fixed_rating: int | None


ANCHOR_LADDER: list[Anchor] = [
    Anchor("random", None),
    Anchor("greedy", None),
    Anchor("sf-1320-d1", None),
    Anchor("sf-1320-d3", None),
    Anchor("sf-1320", 1320),
    Anchor("sf-1500", 1500),
    Anchor("sf-1700", 1700),
    Anchor("sf-1900", 1900),
    Anchor("sf-2100", 2100),
    Anchor("sf-2400", 2400),
]


def anchor_spec(name: str) -> EngineSpec:
    """Return an EngineSpec for an anchor by name."""
    if name in ("random", "greedy"):
        return EngineSpec(
            name=name,
            command=[sys.executable, "-m", "harness.players", name],
            cwd=str(ROOT),
        )

    sf_path = find_stockfish()
    if sf_path is None:
        raise RuntimeError("Stockfish not found. Run 'python -m harness setup' to install it.")

    if name.startswith("sf-1320-d"):
        depth = int(name.split("-d")[1])
        return EngineSpec(
            name=name,
            command=[str(sf_path)],
            cwd=str(ROOT),
            options={"Threads": 1, "Hash": 16, "UCI_LimitStrength": True, "UCI_Elo": 1320},
            limit={"depth": depth},
        )

    if name.startswith("sf-"):
        elo = int(name.split("-")[1])
        return EngineSpec(
            name=name,
            command=[str(sf_path)],
            cwd=str(ROOT),
            options={"Threads": 1, "Hash": 16, "UCI_LimitStrength": True, "UCI_Elo": elo},
        )

    raise ValueError(f"Unknown anchor: {name}")


def resolve_version(ref: str) -> EngineSpec:
    """Resolve a git reference or 'working' to an EngineSpec with its own directory."""
    if ref == "working":
        return EngineSpec(
            name="working",
            command=[sys.executable, "-m", "engine.uci"],
            cwd=str(ROOT),
            sha=None,
        )

    res = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    sha = res.stdout.strip()
    worktree_dir = ROOT / ".harness" / "worktrees" / sha
    if not worktree_dir.exists():
        worktree_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree_dir), sha],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )

    return EngineSpec(
        name=ref,
        command=[sys.executable, "-m", "engine.uci"],
        cwd=str(worktree_dir),
        sha=sha,
    )
