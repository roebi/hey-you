# hey-you

Human-readable CRUD wrapper for recurring OS time triggers.

Translates human time expressions into **cron** or **systemd timers** — whichever your system uses.

```bash
hey-you repeat "HH>1MI<5"           "aider --no-git --message 'health check'"
hey-you repeat "every monday at 9"  "aider-skills run weekly-summary"
hey-you list
hey-you explain "0 9 * * 1"
hey-you resolve "HH>1MI<5"
hey-you remove 3
```

---

## Why

| Tool | Input | Who runs it |
|---|---|---|
| raw `crontab` | `0 9 * * 1` — you must know cron syntax | you |
| `schedule` (PyPI) | Python method chains — runs inside your process | your Python process |
| **`hey-you`** | **`"every monday at 9"` or `"HH>1MI<5"`** | **the OS — process exits** |

The OS owns the timer. `hey-you` is a one-shot translator and crontab/systemd manager.

---

## Installation

```bash
pipx install os-hey-you
```

Requires Python ≥ 3.12.

---

## Placeholder Notation

Built on three POSIX/GNU standards:

- Field names: [strftime(3)](https://man7.org/linux/man-pages/man3/strftime.3.html)
- Relative offsets: [GNU date --date](https://www.gnu.org/software/coreutils/manual/html_node/date-invocation.html)
- Target format: [crontab(5)](https://man7.org/linux/man-pages/man5/crontab.5.html)

Supported tokens (YAGNI — no `YYYY`, no `SS`: standard cron has neither):

| Token | Field       | Range  |
|-------|-------------|--------|
| `MM`  | month       | 01-12  |
| `DD`  | day         | 01-31  |
| `HH`  | hour 24h    | 00-23  |
| `MI`  | minute      | 00-59  |

Each token may carry an offset: `>N` adds, `<N` subtracts.

```
HH>1MI<5    →  hour+1, minute-5
MM>1DD      →  next month, current day
HH MI       →  current hour and minute, no offset
```

---

## Backend Detection

`hey-you` auto-detects your OS scheduler:

```
systemd PID 1?  →  writes ~/.config/systemd/user/hey-you-NNNN.timer
else            →  writes user crontab entry
```

Override: `HEY_YOU_BACKEND=systemd` or `HEY_YOU_BACKEND=cron`.

On Fedora Silverblue, cron requires: `rpm-ostree install cronie` + restart.
systemd is the default and preferred backend.

---

## CRUD

| Operation | Command |
|---|---|
| **C** reate | `hey-you repeat <expr> <command>` |
| **R** ead   | `hey-you list` |
| **R** ead   | `hey-you explain <cron>` |
| **R** ead   | `hey-you resolve <expr>` |
| **D** elete | `hey-you remove <id>` |

Update = `remove` + `repeat`. YAGNI.

---

## Example Use Cases

### Daily health check via aider

```bash
hey-you repeat "HH MI" "aider --no-git --message 'check project health'"
```

### Weekly summary every Monday at 09:00

```bash
hey-you repeat "0 9 * * 1" "aider-skills run weekly-summary"
```

### Understand an existing cron entry

```bash
hey-you explain "0 9 * * 1"
# every Monday at 09:00
```

### Preview a placeholder without writing

```bash
hey-you resolve "HH>1MI<5"
# 25 17 * * *
```

---

## License

MIT — © roebi
