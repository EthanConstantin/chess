import chess
from evaluation import evaluate

"""
TODO
-engine sucks rn lol
-iterative deepening
-Negamax 
-Alpha beta pruning
-play with the piece values
-add simple graphics
"""

board = chess.Board()

fen = "rnbqkbnr/ppp1pppp/8/8/2pPP3/8/PP3PPP/RNBQKBNR w KQkq - 0 1"
board = chess.Board(fen)

# nodes for debugging and performance testing
nodes = 0
def negamax(board, depth, alpha=float("-inf"), beta=float("inf")):  # depth = number of plys
    global nodes
    nodes += 1

    if depth == 0 or board.is_game_over():
        return evaluate(board), []

    
    max_score = float("-inf")
    best_line = []

    for move in board.legal_moves:
        board.push(move)
        child_score, child_line = negamax(board, depth-1, -alpha, -beta)
        score = -child_score
        board.pop()

        # max_score = score if score > max_score else max_score
        if score > max_score:
            max_score = score
            best_line = [move] + child_line

        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return max_score, best_line


best_score, line = negamax(board, 7)
print(f"Best Score: {best_score} \nNodes visited: {nodes}")

line_san = []
temp_board = board.copy()
for move in line:
    line_san.append(temp_board.san(move))
    temp_board.push(move)
    print(temp_board, end="\n\n")

print("Best line:", line_san)