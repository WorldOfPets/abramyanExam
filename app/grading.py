"""Grading helpers: compare program output with expected values."""

from __future__ import annotations

import math

FLOAT_TOLERANCE = 1e-6


def _is_bool(token: str) -> bool:
    return token in {"True", "False"}


def tokens_match(expected: str, actual: str) -> bool:
    """Compare whitespace-separated tokens, tolerating float formatting."""
    expected_tokens = expected.split()
    actual_tokens = actual.split()
    if len(expected_tokens) != len(actual_tokens):
        return False
    for exp, got in zip(expected_tokens, actual_tokens):
        if _is_bool(exp):
            if exp != got:
                return False
            continue
        try:
            exp_number = float(exp)
        except ValueError:
            if exp != got:
                return False
            continue
        try:
            got_number = float(got)
        except ValueError:
            return False
        if math.isnan(exp_number) or math.isnan(got_number):
            return False
        if math.isinf(exp_number) or math.isinf(got_number):
            if exp_number != got_number:
                return False
            continue
        tolerance = FLOAT_TOLERANCE * max(1.0, abs(exp_number))
        if abs(exp_number - got_number) > tolerance:
            return False
    return True


def compare_output(expected: str, actual: str) -> bool:
    return tokens_match(expected, actual)
