import chess

from engine.evaluation import PIECE_VALUES, evaluate


def test_piece_values_in_centipawns():
    assert PIECE_VALUES[chess.PAWN] == 100
    assert PIECE_VALUES[chess.KNIGHT] > PIECE_VALUES[chess.PAWN]
    assert PIECE_VALUES[chess.QUEEN] > PIECE_VALUES[chess.ROOK] > PIECE_VALUES[chess.BISHOP]


def test_start_position_is_balanced():
    assert evaluate(chess.Board()) == 0


def test_score_is_from_side_to_move_perspective():
    # White has an extra queen.
    white_to_move = chess.Board("4k3/8/8/8/8/8/8/3QK3 w - - 0 1")
    black_to_move = chess.Board("4k3/8/8/8/8/8/8/3QK3 b - - 0 1")
    assert evaluate(white_to_move) > 0
    assert evaluate(black_to_move) == -evaluate(white_to_move)


def test_evaluate_returns_int():
    assert isinstance(evaluate(chess.Board()), int)
