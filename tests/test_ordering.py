import chess

import engine.search
from engine.search import Searcher, ordered_moves

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
# White can take the queen on d5 with a pawn (c4) or with the queen (d1), or a pawn on h7.
MVV_LVA = "4k3/7p/8/3q4/2P5/8/8/3QK2R w - - 0 1"


def test_captures_come_before_quiet_moves():
    board = chess.Board(KIWIPETE)
    moves = ordered_moves(board)
    captures = [board.is_capture(m) for m in moves]
    # Once the first quiet move appears, no capture may follow it.
    first_quiet = captures.index(False)
    assert not any(captures[first_quiet:])
    assert sorted(moves, key=str) == sorted(board.legal_moves, key=str)


def test_mvv_lva_order():
    board = chess.Board(MVV_LVA)
    moves = ordered_moves(board)
    pxq = chess.Move.from_uci("c4d5")
    qxq = chess.Move.from_uci("d1d5")
    rxp = chess.Move.from_uci("h1h7")
    assert moves[0] == pxq  # most valuable victim, least valuable attacker
    assert moves.index(qxq) < moves.index(rxp)  # a queen victim beats a pawn victim


def test_promotion_ordered_early():
    board = chess.Board("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
    assert ordered_moves(board)[0] == chess.Move.from_uci("a7a8q")


def test_ordering_reduces_nodes(monkeypatch):
    """Same score as generator order, with fewer nodes: the whole point of ordering."""
    board = chess.Board(KIWIPETE)
    ordered = Searcher().search(board, depth=3)

    monkeypatch.setattr(engine.search, "ordered_moves", lambda b: list(b.legal_moves))
    unordered = Searcher().search(board, depth=3)

    assert ordered.score == unordered.score
    assert ordered.nodes < unordered.nodes
