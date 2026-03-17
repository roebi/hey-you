#!/usr/bin/env python3
"""
cli.py — hey-you subcommand dispatcher.

Subcommands:
  repeat   <expr> <command>   — add a recurring trigger   (C)
  list                        — list all hey-you entries   (R)
  explain  <cron>             — cron string → English      (R)
  resolve  <expr>             — placeholder → cron string  (R, no write)
  remove   <id>               — remove entry by ID         (D)

This is the exact same pattern as a bash case dispatcher:
  case $SUBCOMMAND in
    repeat)  ...  ;;
    list)    ...  ;;
    ...
  esac
"""

import argparse
import sys

from hey_you import __version__
from hey_you.resolve import resolve
from hey_you.explain import explain
from hey_you import backend


def cmd_repeat(args: argparse.Namespace) -> int:
    """Add a recurring trigger: resolve placeholder, write to OS scheduler."""
    try:
        cron_expr = resolve(args.expr)
    except ValueError as e:
        print(f"hey-you: resolve error: {e}", file=sys.stderr)
        return 1

    used_backend = backend.add(cron_expr, args.command)
    print(f"Added [{used_backend}]: {cron_expr}  →  {args.command}")
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    """List all hey-you recurring entries."""
    entries, used_backend = backend.list_entries()
    if not entries:
        print(f"No hey-you entries found (backend: {used_backend})")
        return 0

    print(f"ID  {'CRON':<20}  {'COMMAND'}   (backend: {used_backend})")
    print("-" * 60)
    for e in entries:
        print(f"{e.id:>2}  {e.cron:<20}  {e.command}")
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    """Translate a 5-field cron string to plain English."""
    try:
        sentence = explain(args.cron)
    except ValueError as e:
        print(f"hey-you: explain error: {e}", file=sys.stderr)
        return 1
    print(sentence)
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    """Translate placeholder notation to a cron string (no write)."""
    try:
        cron_expr = resolve(args.expr)
    except ValueError as e:
        print(f"hey-you: resolve error: {e}", file=sys.stderr)
        return 1
    print(cron_expr)
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    """Remove a hey-you entry by its ID (from hey-you list)."""
    ok, used_backend = backend.remove(args.id)
    if not ok:
        print(f"hey-you: no entry with ID {args.id} (backend: {used_backend})",
              file=sys.stderr)
        return 1
    print(f"Removed entry {args.id} (backend: {used_backend})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hey-you",
        description=(
            "Human-readable CRUD wrapper for recurring OS time triggers.\n"
            "Translates human time expressions into cron / systemd timers."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"hey-you {__version__}"
    )

    sub = parser.add_subparsers(dest="subcommand", metavar="SUBCOMMAND")
    sub.required = True

    # repeat
    p_repeat = sub.add_parser("repeat", help="add a recurring trigger  [C]")
    p_repeat.add_argument(
        "expr",
        help='time expression: "every hour", "every monday at 9", or placeholder "HH>1MI<5"',
    )
    p_repeat.add_argument("command", help="shell command to run")

    # list
    sub.add_parser("list", help="list all hey-you entries  [R]")

    # explain
    p_explain = sub.add_parser("explain", help="cron string → plain English  [R]")
    p_explain.add_argument("cron", help='5-field cron string e.g. "0 9 * * 1"')

    # resolve
    p_resolve = sub.add_parser(
        "resolve", help="placeholder → cron string, no write  [R]"
    )
    p_resolve.add_argument("expr", help='placeholder expression e.g. "HH>1MI<5"')

    # remove
    p_remove = sub.add_parser("remove", help="remove entry by ID  [D]")
    p_remove.add_argument("id", type=int, help="entry ID from hey-you list")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # dispatch — mirrors the bash case pattern exactly
    dispatch = {
        "repeat":  cmd_repeat,
        "list":    cmd_list,
        "explain": cmd_explain,
        "resolve": cmd_resolve,
        "remove":  cmd_remove,
    }

    handler = dispatch[args.subcommand]
    sys.exit(handler(args))


if __name__ == "__main__":
    main()
