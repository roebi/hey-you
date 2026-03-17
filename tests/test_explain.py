"""Tests for explain.py — 5-field cron string → plain English sentence."""

import pytest
from hey_you.explain import explain


def test_every_minute():
    assert explain("* * * * *") == "every minute"


def test_every_hour_at_zero():
    assert explain("0 * * * *") == "at minute 0 of every hour"


def test_specific_time():
    assert explain("0 9 * * *") == "at 09:00"


def test_specific_day_of_week():
    assert explain("0 9 * * 1") == "every Monday at 09:00"


def test_specific_day_of_month():
    assert explain("0 9 3 * *") == "on day 3 of every month at 09:00"


def test_specific_month_and_day():
    assert explain("10 20 17 4 *") == "on 17 April at 20:10"


def test_minute_of_every_hour():
    assert explain("15 * * * *") == "at minute 15 of every hour"


def test_every_hour_of_day():
    assert explain("* 14 * * *") == "every minute of hour 14"


def test_wrong_field_count():
    with pytest.raises(ValueError, match="5 cron fields"):
        explain("0 9 * *")


def test_friday():
    assert explain("30 17 * * 5") == "every Friday at 17:30"
