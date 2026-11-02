import subprocess
import sys
from pathlib import Path

import chess

ROOT = Path(__file__).resolve().parent.parent


def run_uci(commands: str) -> list[str]:
    proc = subprocess.run(
        [sys.executable, "-m", "engine.uci"],
        input=commands,
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.splitlines()


def test_handshake():
    lines = run_uci("uci\nisready\nquit\n")
    assert any(line.startswith("id name") for line in lines)
    assert "uciok" in lines
    assert "readyok" in lines


def test_go_depth_from_startpos_with_moves():
    lines = run_uci("uci\nposition startpos moves e2e4 e7e5\ngo depth 2\nquit\n")
    best = [line for line in lines if line.startswith("bestmove")]
    assert len(best) == 1
    board = chess.Board()
    board.push_uci("e2e4")
    board.push_uci("e7e5")
    assert chess.Move.from_uci(best[0].split()[1]) in board.legal_moves
    assert any(line.startswith("info") and " score " in line for line in lines)


def test_go_from_fen_finds_mate():
    lines = run_uci(
        "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1\ngo depth 2\nquit\n"
    )
    assert "bestmove a1a8" in lines
    assert any(" score mate 1" in line for line in lines)


def test_go_without_depth_still_answers():
    # Time-based search arrives in Phase 2. Until then, any `go` must still return a move.
    lines = run_uci("position startpos\ngo wtime 10000 btime 10000\nquit\n")
    assert any(line.startswith("bestmove") for line in lines)
