#!/usr/bin/env python3
"""
resolve.py — translate placeholder notation to a 5-field cron string.

Notation builds on three POSIX/GNU standards:
  - Field names  : strftime(3)   https://man7.org/linux/man-pages/man3/strftime.3.html
  - Relative ops : GNU date -d   https://www.gnu.org/software/coreutils/manual/html_node/date-invocation.html
  - Cron target  : crontab(5)    https://man7.org/linux/man-pages/man5/crontab.5.html

Supported tokens (YAGNI — no YYYY, no SS: standard cron has no year or seconds field):
  MM   current month  (01-12)
  DD   current day    (01-31)
  HH   current hour   (00-23)
  MI   current minute (00-59)

Each token may carry an offset:
  >N   add N
  <N   subtract N

Examples:
  "HH MI"              ->  "30 14 * * *"   (current hour and minute, no offset)
  "HH>1MI<5"           ->  "25 15 * * *"   (hour+1, minute-5)
  "MI HH DD MM"        ->  "30 14 17 3 *"  (fully specified)
  "YYYY<1MM>1DD HH>4MI<20SS>11"  ->  error: YYYY and SS not supported (YAGNI)
"""

import re
from datetime import datetime

# 5-field cron order: minute hour day month day-of-week
_CRON_FIELDS: list[str] = ["MI", "HH", "DD", "MM"]

_TOKEN_PATTERN = re.compile(r"(YYYY|SS|MM|DD|HH|MI)([<>]\d+)?")

_UNSUPPORTED = {"YYYY", "SS"}


def resolve(expr: str, now: datetime | None = None) -> str:
    """
    Resolve a placeholder expression to a 5-field cron string.

    Args:
        expr: placeholder expression e.g. "HH>1MI<5"
        now:  reference datetime (UTC); defaults to datetime.utcnow()

    Returns:
        5-field cron string e.g. "25 15 * * *"

    Raises:
        ValueError: if unsupported tokens (YYYY, SS) are used,
                    or if no valid tokens are found.
    """
    if now is None:
        now = datetime.utcnow()

    base: dict[str, int] = {
        "MM": now.month,
        "DD": now.day,
        "HH": now.hour,
        "MI": now.minute,
    }

    tokens = _TOKEN_PATTERN.findall(expr)

    if not tokens:
        raise ValueError(f"No valid tokens found in expression: {repr(expr)}")

    for placeholder, _ in tokens:
        if placeholder in _UNSUPPORTED:
            raise ValueError(
                f"Token {placeholder!r} is not supported: standard cron has no "
                f"year or seconds field. Remove it (YAGNI)."
            )

    resolved: dict[str, int] = {}
    for placeholder, op in tokens:
        value = base[placeholder]
        if op:
            delta = int(op[1:])
            value = value + delta if op[0] == ">" else value - delta
        resolved[placeholder] = value

    fields = [str(resolved[f]) if f in resolved else "*" for f in _CRON_FIELDS]
    # append wildcard day-of-week
    return " ".join(fields) + " *"
