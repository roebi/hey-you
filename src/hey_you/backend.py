#!/usr/bin/env python3
"""
backend.py — auto-detect OS scheduler backend and provide CRUD operations.

Backends:
  systemd   — preferred on Fedora Silverblue and any systemd-first distro
  crontab   — fallback; requires cronie (rpm-ostree install cronie on Silverblue)

Detection: if systemd is PID 1 → systemd backend, else → crontab backend.
Override: set HEY_YOU_BACKEND=systemd or HEY_YOU_BACKEND=cron in environment.

Crontab reference: https://man7.org/linux/man-pages/man8/cron.8.html
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

# ── tag written into every entry so we can identify hey-you lines ─────────────
_TAG = "# hey-you"


@dataclass
class Entry:
    id: int
    cron: str
    command: str


# ── backend detection ─────────────────────────────────────────────────────────


def detect_backend() -> str:
    """Return 'systemd' or 'cron' based on environment or PID 1."""
    override = os.environ.get("HEY_YOU_BACKEND", "").lower()
    if override in ("systemd", "cron", "crontab"):
        return "systemd" if override == "systemd" else "cron"
    try:
        pid1 = Path("/proc/1/comm").read_text().strip()
        if pid1 == "systemd":
            return "systemd"
    except OSError:
        pass
    return "cron"


# ── crontab backend ───────────────────────────────────────────────────────────


def _crontab_read() -> list[str]:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def _crontab_write(lines: list[str]) -> None:
    content = "\n".join(lines) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".crontab", delete=False) as f:
        f.write(content)
        tmp = f.name
    subprocess.run(["crontab", tmp], check=True)
    Path(tmp).unlink()


def cron_add(cron_expr: str, command: str) -> None:
    lines = _crontab_read()
    lines.append(f"{cron_expr} {command} {_TAG}")
    _crontab_write(lines)


def cron_list() -> list[Entry]:
    lines = _crontab_read()
    entries: list[Entry] = []
    idx = 1
    for line in lines:
        if _TAG in line:
            # strip the tag
            core = line.replace(_TAG, "").strip()
            # first 5 fields are cron, rest is command
            parts = core.split(None, 5)
            if len(parts) >= 6:
                cron_expr = " ".join(parts[:5])
                cmd = parts[5]
                entries.append(Entry(id=idx, cron=cron_expr, command=cmd))
                idx += 1
    return entries


def cron_remove(entry_id: int) -> bool:
    lines = _crontab_read()
    hey_you_lines = [line for line in lines if _TAG in line]
    if entry_id < 1 or entry_id > len(hey_you_lines):
        return False
    target = hey_you_lines[entry_id - 1]
    lines.remove(target)
    _crontab_write(lines)
    return True


# ── systemd backend ───────────────────────────────────────────────────────────

_SYSTEMD_DIR = Path.home() / ".config" / "systemd" / "user"


def _unit_name(idx: int) -> str:
    return f"hey-you-{idx:04d}"


def _next_idx() -> int:
    _SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(_SYSTEMD_DIR.glob("hey-you-*.timer"))
    if not existing:
        return 1
    last = int(existing[-1].stem.split("-")[-1])
    return last + 1


def systemd_add(cron_expr: str, command: str) -> None:
    idx = _next_idx()
    name = _unit_name(idx)
    _SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)

    # convert cron → OnCalendar systemd expression
    on_calendar = _cron_to_on_calendar(cron_expr)

    timer = _SYSTEMD_DIR / f"{name}.timer"
    service = _SYSTEMD_DIR / f"{name}.service"

    timer.write_text(f"""[Unit]
Description=hey-you timer {idx}: {command}

[Timer]
OnCalendar={on_calendar}
Persistent=true

[Install]
WantedBy=timers.target
""")

    service.write_text(f"""[Unit]
Description=hey-you service {idx}: {command}

[Service]
Type=oneshot
ExecStart=/bin/sh -c '{command}'
""")

    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", f"{name}.timer"], check=True)


def systemd_list() -> list[Entry]:
    _SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)
    entries: list[Entry] = []
    for timer_path in sorted(_SYSTEMD_DIR.glob("hey-you-*.timer")):
        idx = int(timer_path.stem.split("-")[-1])
        content = timer_path.read_text()
        # extract OnCalendar value
        cron_expr = ""
        command = ""
        for line in content.splitlines():
            if line.startswith("OnCalendar="):
                cron_expr = line.split("=", 1)[1]
            if line.startswith("Description=hey-you timer"):
                command = line.split(": ", 1)[-1] if ": " in line else ""
        entries.append(Entry(id=idx, cron=cron_expr, command=command))
    return entries


def systemd_remove(entry_id: int) -> bool:
    name = _unit_name(entry_id)
    timer = _SYSTEMD_DIR / f"{name}.timer"
    service = _SYSTEMD_DIR / f"{name}.service"
    if not timer.exists():
        return False
    subprocess.run(
        ["systemctl", "--user", "disable", "--now", f"{name}.timer"], capture_output=True
    )
    timer.unlink(missing_ok=True)
    service.unlink(missing_ok=True)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    return True


def _cron_to_on_calendar(cron: str) -> str:
    """
    Minimal cron → systemd OnCalendar conversion.
    Reference: systemd.time(7)
    Full conversion is a future improvement — covers the common cases.
    """
    parts = cron.strip().split()
    if len(parts) != 5:
        return cron  # pass through unchanged, let systemd validate
    mi, hh, dd, mm, dow = parts

    # wildcards
    mi = "*" if mi == "*" else mi.zfill(2)
    hh = "*" if hh == "*" else hh.zfill(2)
    dd = "*" if dd == "*" else dd
    mm = "*" if mm == "*" else mm
    dow = "*" if dow == "*" else dow

    return f"{dow} {mm}-{dd} {hh}:{mi}:00"


# ── unified public interface ──────────────────────────────────────────────────


def add(cron_expr: str, command: str) -> str:
    backend = detect_backend()
    if backend == "systemd":
        systemd_add(cron_expr, command)
    else:
        cron_add(cron_expr, command)
    return backend


def list_entries() -> tuple[list[Entry], str]:
    backend = detect_backend()
    if backend == "systemd":
        return systemd_list(), backend
    return cron_list(), backend


def remove(entry_id: int) -> tuple[bool, str]:
    backend = detect_backend()
    if backend == "systemd":
        return systemd_remove(entry_id), backend
    return cron_remove(entry_id), backend
