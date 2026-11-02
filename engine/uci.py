"""Universal Chess Interface (UCI) protocol implementation."""

import math
import sys

import chess

from engine.search import MATE_SCORE, Searcher

DEFAULT_DEPTH = 3


def format_score(score: int) -> str:
    """Format an engine score for UCI.

    UCI expects mate scores to be expressed in full moves to mate rather than
    centipawns, with negative numbers indicating the engine is getting mated.
    """
    if abs(score) >= MATE_SCORE - 1000:
        plies = MATE_SCORE - abs(score)
        moves = math.ceil(plies / 2)
        if score < 0:
            moves = -moves
        return f"score mate {moves}"
    return f"score cp {score}"


def parse_go_depth(tokens: list[str]) -> int:
    """Extract search depth from a go command.

    Falls back to a fixed default depth until iterative deepening and clock
    management are introduced in Phase 2.
    """
    if "depth" in tokens:
        idx = tokens.index("depth")
        if idx + 1 < len(tokens):
            try:
                return int(tokens[idx + 1])
            except ValueError:
                pass
    return DEFAULT_DEPTH


def apply_position(current_board: chess.Board, tokens: list[str]) -> chess.Board:
    """Set up the board from a UCI position command.

    Supports both 'startpos' and 'fen' specifications, followed by an optional
    sequence of moves.
    """
    if len(tokens) < 2:
        return current_board

    moves_idx = tokens.index("moves") if "moves" in tokens else len(tokens)

    if tokens[1] == "startpos":
        board = chess.Board()
        moves = tokens[moves_idx + 1:] if moves_idx < len(tokens) else []
    elif tokens[1] == "fen":
        fen_parts = tokens[2:moves_idx]
        fen_str = " ".join(fen_parts)
        moves = tokens[moves_idx + 1:] if moves_idx < len(tokens) else []
        try:
            board = chess.Board(fen_str)
        except ValueError:
            return current_board
    else:
        return current_board

    for move_str in moves:
        try:
            board.push_uci(move_str)
        except ValueError:
            break

    return board


def main() -> None:
    """Run the UCI protocol loop over standard input."""
    board = chess.Board()
    searcher = Searcher()

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        tokens = line.split()
        command = tokens[0]

        if command == "uci":
            print("id name Chess", flush=True)
            print("id author Ethan Constantin", flush=True)
            print("uciok", flush=True)
        elif command == "isready":
            print("readyok", flush=True)
        elif command == "ucinewgame":
            board = chess.Board()
        elif command == "position":
            board = apply_position(board, tokens)
        elif command == "go":
            depth = parse_go_depth(tokens)
            result = searcher.search(board, depth)
            score_str = format_score(result.score)
            time_ms = int(result.time_s * 1000)

            info_parts = [
                f"info depth {result.depth}",
                score_str,
                f"nodes {result.nodes}",
                f"time {time_ms}",
            ]
            if result.pv:
                info_parts.append(f"pv {' '.join(m.uci() for m in result.pv)}")
            print(" ".join(info_parts), flush=True)

            if result.move is not None:
                print(f"bestmove {result.move.uci()}", flush=True)
            else:
                print("bestmove 0000", flush=True)
        elif command == "quit":
            break


if __name__ == "__main__":
    main()
