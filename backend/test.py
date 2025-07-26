import chess

board = chess.Board()

piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}

board.push(chess.Move.from_uci("a2a4"))
board.push(chess.Move.from_uci("b7b5"))
board.push(chess.Move.from_uci("a4b5"))
board.push(chess.Move.from_uci("b8a6"))
board.push(chess.Move.from_uci("a1a6"))

def evaluate(board):
    score = 0
    for piece_type in piece_values:
        score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
    return score

print(board, evaluate(board))