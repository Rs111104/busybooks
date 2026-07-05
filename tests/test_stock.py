# tests/test_stock.py
import datetime
import pytest
from core import stock
from core.stock import NegativeStockError


def test_in_then_out(session, masters):
    wid = masters["widget"].id
    d = datetime.date.today()
    stock.record_movement(session, wid, 10, 0, 60, None, None, d)
    assert stock.current_qty(session, wid) == 10
    stock.record_movement(session, wid, 0, 4, 0, None, None, d)
    assert stock.current_qty(session, wid) == 6


def test_negative_blocked(session, masters):
    wid = masters["widget"].id
    d = datetime.date.today()
    with pytest.raises(NegativeStockError):
        stock.record_movement(session, wid, 0, 5, 0, None, None, d)


def test_weighted_avg_cost(session, masters):
    wid = masters["widget"].id
    d = datetime.date.today()
    stock.record_movement(session, wid, 10, 0, 50, None, None, d)
    stock.record_movement(session, wid, 10, 0, 70, None, None, d)
    assert stock.avg_cost(session, wid) == 60   # (500 + 700) / 20