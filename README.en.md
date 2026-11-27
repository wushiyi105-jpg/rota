# Rota · Small-team shift rota

[![test](https://github.com/wushiyi105-jpg/rota/workflows/test/badge.svg)](https://github.com/wushiyi105-jpg/rota/actions)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Insert a holiday or a sick leave, and the whole month still stays fair.

## Features

- **Six explainable constraints**: fairness (weekends count double), rest gap after a night shift, consecutive-day limit, coverage gaps, leave conflicts, skill mismatch, plus double booking.
- **Minimal-change replanning**: valid shifts from the previous rota are kept, only the days around a new leave are recomputed, and a diff tells you who changed.
- **Skills matched to shifts**: morning needs cashier, night needs night-qualified staff; enforced at solve time and re-checked afterwards.
- **Three exports**: ICS calendar (night shifts end next morning), CSV for Excel, and a short group message.
- **Idempotent job queue**: one digest per month per day, failed pushes stay pending for retry.
- **CLI + Web**: the same operations in a terminal and in the browser.

## Quick start

```bash
uv sync --extra dev
uv run python -m rota seed
uv run python -m rota plan --month 2026-12
uv run python -m rota web            # http://127.0.0.1:8001
uv run python -m rota doctor
```

## Why not just ask a general LLM

1. It cannot count weighted fairness; `weight_of()` does.
2. It forgets hard constraints (night → morning, five-day streaks, leave windows).
3. It has no previous rota, so every edit becomes a full rewrite; `solve(keep=...)` keeps the rest.
4. Its explanation may invent numbers; `domain/guard.py` discards any text containing numbers, dates or names absent from the computed facts.

The model only rewrites the already-computed findings in plain language. Without a key, the offline explanation is used.

**Was the Docker image verified?**
The CI `docker` job runs `docker build .`, starts the container and polls `/health`; Docker is not installed locally, so it was not re-run on the build machine.

## Commands

| Command | What it does |
| --- | --- |
| `rota seed` | load the sample team, skills and leaves |
| `rota plan --month 2026-12 [--json]` | build and store a month |
| `rota show --month ...` | print a stored rota |
| `rota replan --month ... --staff-id ... --start ... --end ...` | add a leave, replan minimally |
| `rota comment --month ...` | model explanation (offline without a key) |
| `rota export --month ... --format ics\|csv\|totals\|message` | export |
| `rota jobs [--enqueue --month ...]` | queue or run due jobs |
| `rota doctor` | config / DB / model / webhook checks |
| `rota web [--port 8001]` | web UI |

Exit codes: 0 ok, 1 runtime error, 2 bad arguments.

## Structure

```
rota/domain/    models, solver, rules/*, engine, diff, guard   (pure, no IO)
rota/ports/     StorePort / LLMPort / NotifierPort
rota/adapters/  sqlite, openai_compat, webhook, export
rota/app/       plan, run, jobs
rota/iface/     cli (Typer), web (FastAPI + Jinja2)
```

## Author

Shiyi · GitHub [@wushiyi105-jpg](https://github.com/wushiyi105-jpg) · 18384198104
