"""Minimal UCI engines for low-end rating anchors (random and greedy).

These engines serve as fixed reference points at the bottom of the rating scale,
where early versions of the chess engine operate.
"""

import random
import sys

import chess

PIECE_VALUES: dict[chess.PieceType, int] = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}


def evaluate_material(board: chess.Board, color: chess.Color) -> int:
    """Calculate material balance from the perspective of color."""
    balance = 0
    for piece in board.piece_map().values():
        val = PIECE_VALUES.get(piece.piece_type, 0)
        if piece.color == color:
            balance += val
        else:
            balance -= val
    return balance


def choose_move(board: chess.Board, mode: str) -> chess.Move | None:
    """Select the best move for the given player mode."""
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    if mode == "random":
        return random.choice(legal_moves)

    # Greedy player: prefer mate-in-1, else maximize material balance after move
    turn = board.turn
    best_score = -float("inf")
    best_moves: list[chess.Move] = []

    for move in legal_moves:
        board.push(move)
        if board.is_checkmate():
            score = 100_000.0
        else:
            score = float(evaluate_material(board, turn))
        board.pop()

        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    return random.choice(best_moves)


def apply_position(board: chess.Board, tokens: list[str]) -> chess.Board:
    """Parse and apply a UCI position command."""
    if len(tokens) < 2:
        return board

    moves_idx = tokens.index("moves") if "moves" in tokens else len(tokens)
    if tokens[1] == "startpos":
        board = chess.Board()
        moves = tokens[moves_idx + 1 :] if moves_idx < len(tokens) else []
    elif tokens[1] == "fen":
        fen_parts = tokens[2:moves_idx]
        board = chess.Board(" ".join(fen_parts))
        moves = tokens[moves_idx + 1 :] if moves_idx < len(tokens) else []
    else:
        return board

    for move_uci in moves:
        try:
            board.push_uci(move_uci)
        except ValueError:
            break

    return board


def run_uci(mode: str) -> None:
    """Run the UCI command loop for the specified player."""
    board = chess.Board()

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        tokens = line.split()
        cmd = tokens[0]

        if cmd == "uci":
            print(f"id name {mode}", flush=True)
            print("id author Harness", flush=True)
            print("uciok", flush=True)
        elif cmd == "isready":
            print("readyok", flush=True)
        elif cmd == "ucinewgame":
            board.reset()
        elif cmd == "position":
            board = apply_position(board, tokens)
        elif cmd == "go":
            move = choose_move(board, mode)
            if move is not None:
                print(f"bestmove {move.uci()}", flush=True)
            else:
                print("bestmove (none)", flush=True)
        elif cmd == "quit":
            break


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "random"
    run_uci(mode)


if __name__ == "__main__":
    main()
