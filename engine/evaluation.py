"""Material evaluation for chess positions."""

import chess

PIECE_VALUES: dict[chess.PieceType, int] = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


def evaluate(board: chess.Board) -> int:
    """Evaluate material balance from the perspective of the side to move.

    Scores are in centipawns so that later phases can combine material cleanly
    with positional bonuses. Negamax requires the score to be relative to the
    player whose turn it is.
    """
    score = 0
    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value
    return score if board.turn == chess.WHITE else -score
