# Benchmarks

Reproducible DRF vs django-bolt load test for this project. The results and how to read them are in the main [README](../README.md#performance-benchmark).

## What it compares
| Build | Code | Server |
|---|---|---|
| **A** | original DRF project (`f19d2e4`), Django 4.2, its own pinned requirements | gunicorn, 2 sync workers (waitress with 8 threads on Windows) |
| **A2** | same DRF code on Django 5.2 (rules out the Django upgrade) | gunicorn, 2 sync workers (waitress with 8 threads on Windows) |
| **B** | django-bolt migration commit (`978727e`), byte-identical responses to A | `runbolt --processes 2` |
| **C** | django-bolt at `HEAD` (or `--c-ref`), with the appliance cache | `runbolt --processes 2` |

Each build gets:
- its own `git worktree`
- its own virtual environment
- its own SQLite database, seeded with the same 50 appliances in the same order

Every build runs with the same settings, from [`bench_settings.py`](bench_settings.py): `DEBUG=False` and logging reduced to warnings.

The endpoints and payloads (in [`payloads/`](payloads)):

| Name | Request |
|---|---|
| `appliances` | `GET /api/v1/power_calculator/appliances/` |
| `v1_calc` | `POST /api/v1/.../calculate/` with the 5-item README example |
| `v2_calc` | `POST /api/v2/.../calculate/` with the 3-item README example |
| `v2_calc_50` | `POST /api/v2/.../calculate/` with 50 items (shows the old one-query-per-item cost) |

## Requirements
- Linux, macOS or Windows, with `git`, [`uv`](https://docs.astral.sh/uv/) and Python 3 on the path. `uv` installs Python 3.11 and 3.12 itself if needed.
- [`oha`](https://github.com/hatoo/oha) on `PATH`, or set `$OHA`. On Linux and Windows x86-64, `setup` downloads it if it's missing.
- On Windows, install `psutil` (`pip install psutil`) so the resource sampler can walk the server process tree; without it the peak RSS / avg CPU columns are skipped.
- About 1 GB of disk for the worktrees and environments (in `benchmarks/.work/`, which git ignores).

## Running it
From the repository root (use `python` on Windows, `python3` on Linux/macOS):
```bash
python benchmarks/bench.py setup                  # once: worktrees, environments, databases
python benchmarks/bench.py run                    # ~18 min: 4 builds x 4 endpoints x (5 s warm-up + 3 x 20 s)
python benchmarks/bench.py queries                # DB queries per request, per build
python benchmarks/bench.py report                 # markdown tables for the README
```

Results go to `benchmarks/results/<label>/`. The default label is today's date; choose your own with `--label`.

| File | Contents |
|---|---|
| `results_<build>.json` | Per endpoint: median req/s, p50/p95/p99 latency (ms), error %, the req/s of each run, peak memory and average CPU of the server processes |
| `queries.json` | SQL statements per request, counted on every thread (Bolt runs handlers on worker threads) |
| `response_<build>_<endpoint>.json` | The body each build returned, so you can check they match |
| `meta.json` | Run parameters and machine details |

Useful options:
```bash
python benchmarks/bench.py run --builds A B           # only some builds
python benchmarks/bench.py run --duration 60s --runs 5 --concurrency 100
python benchmarks/bench.py setup --c-ref my-branch    # benchmark another commit as C
BENCH_WORK=/tmp/bench python benchmarks/bench.py setup    # keep working files elsewhere (set BENCH_WORK=C:\bench on Windows)
```

To remove the working files:
```bash
git worktree remove --force benchmarks/.work/A    # likewise B and C
rm -rf benchmarks/.work
```

## Fairness notes
- **Same machine, same resources:** all builds use the same machine, database contents, payloads, warm-up, duration and concurrency. Each server gets 2 processes/workers.
- **Correctness first:** before load testing, each build's response to every payload is saved. A, A2 and B return identical bodies. C's calculation numbers differ because the sizing formulas were corrected later.
- **Load generator competes for CPU:** oha runs on the same machine as the servers, so they share CPU. Run on a quiet machine, and compare ratios rather than absolute numbers.
- **SQLite over localhost:** with Postgres and real network latency, requests spend more time outside the framework. Absolute numbers drop, and the framework-only gap likely narrows.
- **Framework-only comparison:** the `appliances` endpoint makes one query in both A and B, so A vs B there isolates the framework. The calculate endpoints also include the move from one query per item to a single query.

## Stored results
- [`results/2026-09-26/`](results/2026-09-26): the run quoted in the main README. Measured on a 4 vCPU (Intel Xeon @ 2.10 GHz) cloud container with oha 1.16. Build C was commit `40bebdf`.
