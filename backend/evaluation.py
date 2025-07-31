import chess
""" 
TODO: 
Add the following to the heuristic evaluation function:
-Checkmate
-Check
-Passed pawn
-Isolated pawn
-Doubled pawn
-Stuck pawn (when there is an opposing pawn opposite it and no other pawns can challenge the opposite pawn)
-Mobility (Number of legal moves available to the player)
-outpost squares
-Continuity (if there is a payoff for a type of move ie outpost squares make a smaller payoff for attacking that square)
-Make each piece be worth differently depending on its location on the board
"""

piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}

def evaluate(board):
    score = 0
    for piece_type in piece_values:
        score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
    return score