"""Telemetry persistence, environment capture, and PGN logging.

Records benchmark results to telemetry/results.jsonl and saves full match
records to telemetry/games/.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re

import chess

from harness.stockfish import STOCKFISH_TAG

ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = ROOT / "telemetry" / "results.jsonl"
ANCHORS_PATH = ROOT / "telemetry" / "anchors.json"
GAMES_DIR = ROOT / "telemetry" / "games"


def append_record(record: dict, path: Path | str = RESULTS_PATH) -> None:
    """Append a telemetry record as a JSON line, ensuring timestamp exists."""
    if "timestamp" not in record:
        record["timestamp"] = datetime.now(timezone.utc).isoformat()

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_records(path: Path | str = RESULTS_PATH) -> list[dict]:
    """Load all records from a jsonl file; returns an empty list if missing."""
    file_path = Path(path)
    if not file_path.exists():
        return []

    records = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def environment() -> dict:
    """Capture execution environment metadata for reproducible telemetry."""
    return {
        "python": platform.python_version(),
        "chess": getattr(chess, "__version__", ""),
        "platform": platform.platform(),
        "cpu": platform.processor(),
        "cpu_count": os.cpu_count(),
        "stockfish": STOCKFISH_TAG,
    }


def save_pgn(games, name: str) -> Path:
    """Save match games to a timestamped PGN file in GAMES_DIR."""
    GAMES_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\-.]", "_", name)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filepath = GAMES_DIR / f"{safe_name}_{ts}.pgn"

    entries = []
    for g in games:
        if hasattr(g, "pgn"):
            entries.append(g.pgn)
        else:
            entries.append(str(g))

    content = "\n\n".join(entries).strip() + "\n"
    filepath.write_text(content, encoding="utf-8")
    return filepath
