#!/usr/bin/env python3
"""
explain.py — translate a 5-field cron string to a plain English sentence.

Reference: crontab(5)  https://man7.org/linux/man-pages/man5/crontab.5.html

Field positions: MI HH DD MM DOW
"""

DAYS_OF_WEEK = {
    "0": "Sunday",
    "7": "Sunday",
    "1": "Monday",
    "2": "Tuesday",
    "3": "Wednesday",
    "4": "Thursday",
    "5": "Friday",
    "6": "Saturday",
}

MONTHS = {
    "1": "January",
    "2": "February",
    "3": "March",
    "4": "April",
    "5": "May",
    "6": "June",
    "7": "July",
    "8": "August",
    "9": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}


def explain(cron: str) -> str:
    """
    Translate a 5-field cron string to a plain English sentence.

    Args:
        cron: 5-field cron string e.g. "0 9 * * 1"

    Returns:
        Plain English description e.g. "every Monday at 09:00"

    Raises:
        ValueError: if the string does not have exactly 5 fields.
    """
    fields = cron.strip().split()
    if len(fields) != 5:
        raise ValueError(f"Expected 5 cron fields, got {len(fields)}: {repr(cron)}")

    mi, hh, dd, mm, dow = fields

    parts: list[str] = []

    # day-of-week
    if dow != "*":
        day_name = DAYS_OF_WEEK.get(dow, f"day-of-week={dow}")
        parts.append(f"every {day_name}")

    # month + day
    if mm != "*" and dd != "*":
        month_name = MONTHS.get(mm, f"month {mm}")
        parts.append(f"on {dd} {month_name}")
    elif mm != "*":
        month_name = MONTHS.get(mm, f"month {mm}")
        parts.append(f"every {month_name}")
    elif dd != "*":
        parts.append(f"on day {dd} of every month")

    # time
    if hh != "*" and mi != "*":
        parts.append(f"at {int(hh):02d}:{int(mi):02d}")
    elif hh != "*":
        parts.append(f"every minute of hour {int(hh):02d}")
    elif mi != "*":
        parts.append(f"at minute {mi} of every hour")
    else:
        parts.append("every minute")

    if not parts:
        return "every minute"

    return " ".join(parts)
