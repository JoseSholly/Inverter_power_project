#!/usr/bin/env python3
"""DRF vs django-bolt benchmark for this project.

    python benchmarks/bench.py setup     # check out builds, create envs, seed DBs (once)
    python benchmarks/bench.py run       # load-test every build with oha
    python benchmarks/bench.py queries   # DB queries per request, per build
    python benchmarks/bench.py report    # markdown tables from the latest results

Builds (see benchmarks/README.md):
    A   original DRF code, Django 4.2 (its own pinned requirements), gunicorn (waitress on Windows)
    A2  same DRF code on Django 5.2, gunicorn (waitress on Windows)
    B   django-bolt migration commit (same responses as A), runbolt
    C   django-bolt at --c-ref (default HEAD), runbolt

Needs git, uv and oha (on PATH, or $OHA, or downloaded by setup on Linux/Windows x86-64).
On Windows, `psutil` must be importable (pip install psutil) for the resource sampler.
"""
import argparse
import ast
import json
import os
import platform
import shutil
import signal
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

IS_WINDOWS = os.name == "nt"
VENV_BIN = "Scripts" if IS_WINDOWS else "bin"
EXE = ".exe" if IS_WINDOWS else ""

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
WORK = Path(os.environ.get("BENCH_WORK", HERE / ".work"))
RESULTS = HERE / "results"
PORT = 8100
BASE = f"http://127.0.0.1:{PORT}"

DRF_REF = "f19d2e4"          # original DRF project
BOLT_MIGRATION_REF = "978727e"  # migration only: byte-identical responses to DRF
# gunicorn doesn't run on Windows (needs fcntl); waitress is the substitute.
A2_REQUIREMENTS = [
    "django==5.2.17", "djangorestframework==3.18.1", "drf-yasg==1.21.15", "django-rest-swagger==2.2.0",
    "coreapi==2.3.3", "setuptools==69.5.1", "django-jazzmin==3.0.5",
    "django-cors-headers==4.9.0", "whitenoise==6.12.0", "python-decouple==3.8", "python-dotenv==1.2.3",
] + (["waitress"] if IS_WINDOWS else ["gunicorn==26.2.0"])

OHA_URLS = {
    ("Linux", "x86_64"):  "https://github.com/hatoo/oha/releases/latest/download/oha-linux-amd64",
    ("Linux", "AMD64"):   "https://github.com/hatoo/oha/releases/latest/download/oha-linux-amd64",
    ("Windows", "AMD64"): "https://github.com/hatoo/oha/releases/latest/download/oha-windows-amd64.exe",
    ("Windows", "x86_64"): "https://github.com/hatoo/oha/releases/latest/download/oha-windows-amd64.exe",
}
OHA_LOCAL = "oha.exe" if IS_WINDOWS else "oha"

ENDPOINTS = [  # name, method, path, payload
    ("appliances", "GET", "/api/v1/power_calculator/appliances/", None),
    ("v1_calc", "POST", "/api/v1/power_calculator/calculate/", "v1.json"),
    ("v2_calc", "POST", "/api/v2/power_calculator/calculate/", "v2.json"),
    ("v2_calc_50", "POST", "/api/v2/power_calculator/calculate/", "v2_50.json"),
]
ENDPOINT_LABELS = {
    "appliances": "`GET appliances/`",
    "v1_calc": "`POST v1 calculate` (5 items)",
    "v2_calc": "`POST v2 calculate` (3 items)",
    "v2_calc_50": "`POST v2 calculate` (50 items)",
}
ENV_COMMON = {
    "SECRET_KEY": "bench", "CORS_ALLOWED_ORIGINS": "http://bench.local",
    "CSRF_TRUSTED_ORIGINS": "http://bench.local", "DJANGO_SETTINGS_MODULE": "bench_settings",
}


def venv_python(env_dir):
    return env_dir / VENV_BIN / f"python{EXE}"


def venv_exe(env_dir, name):
    return env_dir / VENV_BIN / f"{name}{EXE}"


# ---------------------------------------------------------------- builds
def builds():
    """name -> (project dir, python, server command)."""
    def wsgi_server(env):
        if IS_WINDOWS:
            return [str(venv_exe(env, "waitress-serve")), "--host=127.0.0.1", f"--port={PORT}",
                    "--threads=8", "inverter_project.wsgi:application"]
        return [str(venv_exe(env, "gunicorn")), "inverter_project.wsgi", "-w", "2",
                "-b", f"127.0.0.1:{PORT}", "--log-level", "warning"]

    def runbolt(py):
        return [str(py), "manage.py", "runbolt", "--host", "127.0.0.1", "--port", str(PORT), "--processes", "2"]

    a_dir = WORK / "A" / "inverter_project"
    b_dir = WORK / "B" / "inverter_project"
    c_dir = WORK / "C" / "inverter_project"
    return {
        "A":  (a_dir, venv_python(WORK / "envA"),  wsgi_server(WORK / "envA")),
        "A2": (a_dir, venv_python(WORK / "envA2"), wsgi_server(WORK / "envA2")),
        "B":  (b_dir, venv_python(b_dir / ".venv"), runbolt(venv_python(b_dir / ".venv"))),
        "C":  (c_dir, venv_python(c_dir / ".venv"), runbolt(venv_python(c_dir / ".venv"))),
    }


def build_env(name, project_dir):
    return {**os.environ, **ENV_COMMON, "BENCH_DB": str(WORK / f"{name}.db"),
            "PYTHONPATH": f"{HERE}{os.pathsep}{project_dir}"}


def sh(*cmd, **kwargs):
    shown = ["<script>" if "\n" in str(c) else str(c) for c in cmd]
    print("+", " ".join(shown), flush=True)
    return subprocess.run([str(c) for c in cmd], check=True, **kwargs)


def oha_path():
    for candidate in (os.environ.get("OHA"), shutil.which("oha"), WORK / OHA_LOCAL):
        if candidate and Path(candidate).exists():
            return str(candidate)
    sys.exit("oha not found: install it (https://github.com/hatoo/oha), set $OHA, or run `bench.py setup`.")


def catalog_names():
    """The 50 default appliances, read from the current checkout's catalog."""
    tree = ast.parse((REPO / "inverter_project/power_calculator/appliance_catalog.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "DEFAULT_APPLIANCES":
            return list(ast.literal_eval(node.value))
    raise RuntimeError("DEFAULT_APPLIANCES not found")


SEED = """
import json, os, django
django.setup()
from power_calculator.models import Appliance
for name in json.loads(os.environ["NAMES"]):
    Appliance.objects.get_or_create(name=name)
assert Appliance.objects.count() == len(json.loads(os.environ["NAMES"]))
print(os.environ["BENCH_DB"], Appliance.objects.count(), "appliances")
"""


def _worktree_remove(target):
    """Remove a git worktree; if git no longer knows about it, wipe the directory manually."""
    result = subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force", str(target)],
                            capture_output=True, text=True)
    if result.returncode == 0:
        return
    # Stale directory left over from a previous partial run — git worktree list forgot it.
    shutil.rmtree(target, ignore_errors=True)
    subprocess.run(["git", "-C", str(REPO), "worktree", "prune"], check=False)


def cmd_setup(args):
    if IS_WINDOWS and psutil is None:
        print("Warning: psutil not importable — resource sampling (peak RSS / avg CPU) will be skipped on Windows.\n"
              "         Install with:  pip install psutil", flush=True)
    WORK.mkdir(parents=True, exist_ok=True)
    for name, ref in (("A", DRF_REF), ("B", BOLT_MIGRATION_REF), ("C", args.c_ref)):
        target = WORK / name
        if target.exists():
            _worktree_remove(target)
        sh("git", "-C", REPO, "worktree", "add", "--detach", target, ref)

    # A: the original pinned requirements (Python 3.11; drf-yasg there still needs pkg_resources).
    reqs = WORK / "requirements-A.txt"
    reqs.write_bytes(subprocess.run(["git", "-C", str(REPO), "show", f"{DRF_REF}:inverter_project/requirements.txt"],
                                    check=True, capture_output=True).stdout)
    sh("uv", "venv", "-q", "--clear", "-p", "3.11", WORK / "envA")
    extra_a = ["waitress"] if IS_WINDOWS else []
    sh("uv", "pip", "install", "-q", "--python", venv_python(WORK / "envA"),
       "-r", reqs, "setuptools<70", *extra_a)
    # A2: same DRF code on Django 5.2.
    sh("uv", "venv", "-q", "--clear", "-p", "3.12", WORK / "envA2")
    sh("uv", "pip", "install", "-q", "--python", venv_python(WORK / "envA2"), *A2_REQUIREMENTS)
    # B, C: their own locked environments.
    for name in ("B", "C"):
        sh("uv", "sync", "-q", "--frozen", cwd=WORK / name / "inverter_project")

    names = json.dumps(catalog_names())
    for name, (project_dir, python, _) in builds().items():
        db = WORK / f"{name}.db"
        db.unlink(missing_ok=True)
        env = build_env(name, project_dir)
        sh(python, "manage.py", "migrate", "-v", "0", cwd=project_dir, env=env)
        sh(python, "-c", SEED, cwd=project_dir, env={**env, "NAMES": names})

    if not (os.environ.get("OHA") or shutil.which("oha") or (WORK / OHA_LOCAL).exists()):
        key = (platform.system(), platform.machine())
        if key in OHA_URLS:
            dest = WORK / OHA_LOCAL
            urllib.request.urlretrieve(OHA_URLS[key], dest)
            if not IS_WINDOWS:
                dest.chmod(0o755)
        else:
            print(f"Install oha yourself for {key}: https://github.com/hatoo/oha")
    print("\nSetup done. Next: python benchmarks/bench.py run")


# ---------------------------------------------------------------- run
def _tree_pids(root):
    if psutil is not None:
        try:
            proc = psutil.Process(root)
            return [root] + [c.pid for c in proc.children(recursive=True)]
        except psutil.NoSuchProcess:
            return [root]
    # POSIX fallback via ps
    rows = subprocess.run(["ps", "-eo", "pid=,ppid="], capture_output=True, text=True).stdout.split("\n")
    children = {}
    for row in rows:
        if row.strip():
            pid, ppid = map(int, row.split())
            children.setdefault(ppid, []).append(pid)
    pids, stack = [], [root]
    while stack:
        pid = stack.pop()
        pids.append(pid)
        stack += children.get(pid, [])
    return pids


def _sample_resources(root, stop, samples):
    if psutil is not None:
        procs = {}
        while not stop.is_set():
            for pid in _tree_pids(root):
                if pid not in procs:
                    try:
                        procs[pid] = psutil.Process(pid)
                        procs[pid].cpu_percent(interval=None)  # prime the counter
                    except psutil.NoSuchProcess:
                        pass
            rss_kb = 0
            cpu = 0.0
            for pid, p in list(procs.items()):
                try:
                    rss_kb += p.memory_info().rss // 1024
                    cpu += p.cpu_percent(interval=None)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    procs.pop(pid, None)
            samples.append((rss_kb, cpu))
            time.sleep(1)
        return
    if IS_WINDOWS:
        samples.append((0, 0.0))  # no psutil on Windows: skip sampling
        return
    while not stop.is_set():
        pids = ",".join(map(str, _tree_pids(root)))
        rows = subprocess.run(["ps", "-o", "rss=,pcpu=", "-p", pids], capture_output=True, text=True).stdout.split("\n")
        rows = [row.split() for row in rows if row.strip()]
        samples.append((sum(int(r[0]) for r in rows), sum(float(r[1]) for r in rows)))
        time.sleep(1)


def _oha(method, path, payload, duration, concurrency):
    cmd = [oha_path(), "--no-tui", "--output-format", "json", "-z", duration, "-c", str(concurrency), "-m", method,
           BASE + path]
    if payload:
        cmd += ["-D", str(HERE / "payloads" / payload), "-H", "content-type: application/json"]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)


def _wait_until_up():
    for _ in range(240):
        try:
            urllib.request.urlopen(BASE + ENDPOINTS[0][2], timeout=1)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("server did not start")


def _spawn_server(cmd, cwd, env, stderr):
    if IS_WINDOWS:
        return subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=stderr,
                                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    return subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=stderr,
                            start_new_session=True)


def _terminate_server(server):
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(server.pid)], capture_output=True)
    else:
        try:
            os.killpg(server.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        server.wait(timeout=30)
    except subprocess.TimeoutExpired:
        server.kill()


def run_build(name, args, out_dir):
    project_dir, _, server_cmd = builds()[name]
    log = open(out_dir / f"{name}.server.log", "w")
    server = _spawn_server(server_cmd, cwd=project_dir, env=build_env(name, project_dir), stderr=log)
    results = {}
    try:
        _wait_until_up()
        for endpoint, method, path, payload in ENDPOINTS:
            data = (HERE / "payloads" / payload).read_bytes() if payload else None
            request = urllib.request.Request(BASE + path, data=data, method=method,
                                             headers={"content-type": "application/json"})
            response = urllib.request.urlopen(request)
            (out_dir / f"response_{name}_{endpoint}.json").write_bytes(response.read())

            _oha(method, path, payload, args.warmup, args.concurrency)
            runs, samples = [], []
            for _ in range(args.runs):
                stop = threading.Event()
                sampler = threading.Thread(target=_sample_resources, args=(server.pid, stop, samples))
                sampler.start()
                result = _oha(method, path, payload, args.duration, args.concurrency)
                stop.set()
                sampler.join()
                codes = result.get("statusCodeDistribution", {})
                total = sum(codes.values()) or 1
                ok = sum(count for code, count in codes.items() if code.startswith("2"))
                pct = result["latencyPercentiles"]
                runs.append({"rps": result["summary"]["requestsPerSec"], "p50": pct["p50"] * 1000,
                             "p95": pct["p95"] * 1000, "p99": pct["p99"] * 1000,
                             "err": 100 * (1 - ok / total), "n": total})
            median = {key: statistics.median(run[key] for run in runs) for key in runs[0]}
            median["rps_runs"] = [round(run["rps"]) for run in runs]
            median["peak_rss_mb"] = (max(s[0] for s in samples) / 1024) if samples else 0
            median["avg_cpu_pct"] = statistics.mean(s[1] for s in samples) if samples else 0
            results[endpoint] = median
            print(f"{name:3} {endpoint:11} {median['rps']:8.0f} req/s  p50 {median['p50']:6.1f} ms  "
                  f"p99 {median['p99']:6.1f} ms  errors {median['err']:.2f}%  runs {median['rps_runs']}", flush=True)
    finally:
        _terminate_server(server)
        log.close()
    (out_dir / f"results_{name}.json").write_text(json.dumps(results, indent=1))


def cmd_run(args):
    out_dir = RESULTS / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {"warmup": args.warmup, "duration": args.duration, "runs": args.runs, "concurrency": args.concurrency,
            "cpu_count": os.cpu_count(), "platform": platform.platform(), "oha": subprocess.run(
                [oha_path(), "--version"], capture_output=True, text=True).stdout.strip()}
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=1))
    for name in args.builds:
        run_build(name, args, out_dir)
    print(f"\nResults in {out_dir}. Next: python benchmarks/bench.py report --label {args.label}")


# ---------------------------------------------------------------- queries
QUERY_COUNTER = """
import json, os, sys, threading
import django
django.setup()
from django.db.backends import utils

count, lock = [0], threading.Lock()
original = utils.CursorWrapper.execute
def counting(self, *a, **k):  # counts SQL on every thread and connection (Bolt uses worker threads)
    with lock:
        count[0] += 1
    return original(self, *a, **k)
utils.CursorWrapper.execute = counting

endpoints, payload_dir = json.loads(os.environ["ENDPOINTS"]), os.environ["PAYLOADS"]
try:
    from django_bolt.testing import TestClient
    from inverter_project.api import api
    client = TestClient(api).__enter__()
    def call(method, path, payload):
        if payload:
            body = open(os.path.join(payload_dir, payload), "rb").read()
            return client.post(path, content=body, headers={"content-type": "application/json"})
        return client.get(path)
except ImportError:  # DRF build
    from django.test import Client
    client = Client()
    def call(method, path, payload):
        if payload:
            body = open(os.path.join(payload_dir, payload)).read()
            return client.post(path, body, content_type="application/json")
        return client.get(path)

out = {}
for name, method, path, payload in endpoints:
    call(method, path, payload)  # warm-up: caches, lazy imports
    count[0] = 0
    response = call(method, path, payload)
    assert response.status_code in (200, 201), (name, response.status_code)
    out[name] = count[0]
print(json.dumps(out))
"""


def cmd_queries(args):
    out_dir = RESULTS / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name in args.builds:
        project_dir, python, _ = builds()[name]
        env = {**build_env(name, project_dir), "ENDPOINTS": json.dumps(ENDPOINTS), "PAYLOADS": str(HERE / "payloads")}
        output = subprocess.run([str(python), "-c", QUERY_COUNTER], cwd=project_dir, env=env,
                                capture_output=True, text=True, check=True).stdout
        counts[name] = json.loads(output.strip().splitlines()[-1])
        print(name, counts[name])
    (out_dir / "queries.json").write_text(json.dumps(counts, indent=1))


# ---------------------------------------------------------------- report
def cmd_report(args):
    out_dir = RESULTS / args.label
    results = {p.stem.removeprefix("results_"): json.loads(p.read_text())
               for p in sorted(out_dir.glob("results_*.json"))}
    if not results:
        sys.exit(f"No results in {out_dir}")
    names = [n for n in ("A", "A2", "B", "C") if n in results]
    base = results.get("A")

    def ratio(name, endpoint):
        if not base or name == "A":
            return ""
        return f" ({results[name][endpoint]['rps'] / base[endpoint]['rps']:.1f}x)"

    print("| Endpoint | " + " | ".join(names) + " |")
    print("|---|" + "---|" * len(names))
    for endpoint in ENDPOINT_LABELS:
        cells = [f"{results[n][endpoint]['rps']:,.0f} req/s{ratio(n, endpoint)}" for n in names]
        print(f"| {ENDPOINT_LABELS[endpoint]} | " + " | ".join(cells) + " |")
    print("\nLatency p50 / p95 / p99 (ms)\n")
    print("| Endpoint | " + " | ".join(names) + " |")
    print("|---|" + "---|" * len(names))
    for endpoint in ENDPOINT_LABELS:
        cells = ["{p50:.1f} / {p95:.1f} / {p99:.1f}".format(**results[n][endpoint]) for n in names]
        print(f"| {ENDPOINT_LABELS[endpoint]} | " + " | ".join(cells) + " |")
    worst = max(r[e]["err"] for r in results.values() for e in r)
    print(f"\nHighest error rate across all runs: {worst:.2f}%")
    queries_file = out_dir / "queries.json"
    if queries_file.exists():
        queries = json.loads(queries_file.read_text())
        print("\nDB queries per request\n")
        print("| Endpoint | " + " | ".join(queries) + " |")
        print("|---|" + "---|" * len(queries))
        for endpoint in ENDPOINT_LABELS:
            print(f"| {ENDPOINT_LABELS[endpoint]} | " + " | ".join(str(queries[n][endpoint]) for n in queries) + " |")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("setup", help="check out builds, create environments, seed databases")
    setup.add_argument("--c-ref", default="HEAD", help="git ref for build C (default HEAD)")
    for name in ("run", "queries", "report"):
        p = sub.add_parser(name)
        p.add_argument("--label", default=time.strftime("%Y-%m-%d"), help="results folder name")
        if name != "report":
            p.add_argument("--builds", nargs="+", default=["A", "A2", "B", "C"], choices=["A", "A2", "B", "C"])
        if name == "run":
            p.add_argument("--warmup", default="5s")
            p.add_argument("--duration", default="20s")
            p.add_argument("--runs", type=int, default=3)
            p.add_argument("--concurrency", type=int, default=50)
    args = parser.parse_args()
    {"setup": cmd_setup, "run": cmd_run, "queries": cmd_queries, "report": cmd_report}[args.command](args)


if __name__ == "__main__":
    main()
