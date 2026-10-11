"""Paise helpers. Money is an integer number of paise everywhere; rupees exist only on screen."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def rupees(amount: int | str) -> int:
    """Rupees to paise: ``rupees(980) == 98000``, ``rupees("12.50") == 1250``."""
    return int((Decimal(str(amount)) * 100).to_integral_value(ROUND_HALF_UP))


def from_rupees(value: float | int | str) -> int:
    """Paise from a rupee figure a model returned (it may be a float like 980.0)."""
    return rupees(str(value))


def group_indian(n: int) -> str:
    """Indian digit grouping: 25100000 -> '2,51,00,000'."""
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    pairs = []
    while len(head) > 2:
        pairs.insert(0, head[-2:])
        head = head[:-2]
    return ",".join([head, *pairs, tail]) if head else ",".join([*pairs, tail])


def inr(paise: int) -> str:
    """Display form used in events and letters: ``inr(251000000) == '₹25,10,000.00'``."""
    sign = "-" if paise < 0 else ""
    whole, frac = divmod(abs(paise), 100)
    return f"{sign}₹{group_indian(whole)}.{frac:02d}"
