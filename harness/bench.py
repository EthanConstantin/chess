"""Standard position benchmark for engine speed and node efficiency.

Evaluates engines on 8 fixed, diverse positions at a constant depth, reporting
node count, elapsed wall-clock time, and nodes per second (NPS).
"""

import time

import chess
import chess.engine

from harness.versions import EngineSpec

BENCH_POSITIONS: list[str] = [
    # 1. Starting position
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    # 2. Open middlegame (Italian)
    "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 7",
    # 3. Closed middlegame (King's Indian)
    "r2q1rk1/1ppnbppp/p2p1nb1/3Pp3/2P1P1P1/2N1BN1P/PP2BP2/R2Q1RK1 b - - 0 11",
    # 4. Tactical position
    "r1b1k2r/ppppqppp/2n5/8/1bP2Bn1/2N2N2/PP2PPPP/R2QKB1R w KQkq - 4 8",
    # 5. Rook endgame
    "8/5pk1/4p1p1/7p/7P/4r1P1/5PK1/8 w - - 0 45",
    # 6. Pawn endgame
    "8/5p2/4p1p1/4k2p/7P/4K1P1/5P2/8 w - - 0 40",
    # 7. Queen vs pieces
    "r1b2rk1/pp3ppp/2n5/8/8/2N2N2/PP2BPPP/3Q1RK1 w - - 0 15",
    # 8. Kiwipete
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
]


def run_bench(spec: EngineSpec, depth: int = 4) -> dict:
    """Run a fixed-depth search over the benchmark positions and report performance."""
    engine = chess.engine.SimpleEngine.popen_uci(spec.command, cwd=spec.cwd)
    if spec.options:
        engine.configure(spec.options)

    positions = []
    try:
        for fen in BENCH_POSITIONS:
            board = chess.Board(fen)
            t0 = time.perf_counter()
            info_limit = chess.engine.Limit(depth=depth)
            play_res = engine.play(board, info_limit, info=chess.engine.INFO_ALL)
            time_s = time.perf_counter() - t0

            nodes = play_res.info.get("nodes", 0)
            nps = nodes / time_s if time_s > 0 else 0.0

            positions.append({
                "fen": fen,
                "nodes": nodes,
                "time_s": time_s,
                "nps": nps,
            })
    finally:
        try:
            engine.quit()
        except Exception:
            pass

    total_nodes = sum(p["nodes"] for p in positions)
    total_time = sum(p["time_s"] for p in positions)
    total_nps = total_nodes / total_time if total_time > 0 else 0.0

    return {
        "depth": depth,
        "positions": positions,
        "nodes": total_nodes,
        "time_s": total_time,
        "nps": total_nps,
    }
