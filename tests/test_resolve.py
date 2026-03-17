"""Tests for resolve.py — placeholder notation → 5-field cron string."""

from datetime import datetime

import pytest

from hey_you.resolve import resolve

# fixed reference datetime: 2026-03-17 16:30 UTC
NOW = datetime(2026, 3, 17, 16, 30)


def test_single_hour():
    assert resolve("HH", NOW) == "* 16 * * *"


def test_single_minute():
    assert resolve("MI", NOW) == "30 * * * *"


def test_hour_and_minute():
    assert resolve("HH MI", NOW) == "30 16 * * *"


def test_hour_plus_offset():
    assert resolve("HH>1", NOW) == "* 17 * * *"


def test_minute_minus_offset():
    assert resolve("MI<5", NOW) == "25 * * * *"


def test_combined_offsets():
    # HH>1=17, MI<5=25
    assert resolve("HH>1MI<5", NOW) == "25 17 * * *"


def test_full_expression():
    # MM>1=4, DD=17, HH>4=20, MI<20=10
    assert resolve("MM>1DD HH>4MI<20", NOW) == "10 20 17 4 *"


def test_no_tokens_raises():
    with pytest.raises(ValueError, match="No valid tokens"):
        resolve("every hour", NOW)


def test_yyyy_raises():
    with pytest.raises(ValueError, match="YYYY"):
        resolve("YYYY<1MM>1", NOW)


def test_ss_raises():
    with pytest.raises(ValueError, match="SS"):
        resolve("HH MI SS>11", NOW)


def test_your_example():
    # from the original conversation:
    # YYYY<1MM>1DD-HH>4MI<20SS>11 against 2026-03-17 16:30
    # YYYY and SS must be stripped first — they raise
    # clean version without YYYY and SS:
    result = resolve("MM>1DD HH>4MI<20", NOW)
    assert result == "10 20 17 4 *"
