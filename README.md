# Inverter Power Project API

A stateless API that sizes a home backup power system. You send a list of appliances and get back the inverter rating, battery bank, solar array and charge current you need. Nothing is saved: each request is calculated and returned straight away.

There are two versions of the calculation:

- **v1** uses **one backup time for all appliances** and only accepts standard component sizes (12/24/48 V systems, 150–250 Ah batteries, 300–450 W panels).
- **v2** lets **each appliance have its own backup time**. It accepts any system voltage that is a multiple of 12 V, and any positive battery capacity and panel wattage.

Apart from how energy demand is worked out, both versions use the **same sizing model** (`api/common/sizing.py`). If every appliance has the same backup time, v1 and v2 return identical results.

## Table of Contents
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [API Documentation](#api-documentation)
- [Endpoints](#endpoints)
- [Request Fields](#request-fields)
- [Examples](#examples)
- [Calculation Formulas](#calculation-formulas)
- [Worked Scenarios](#worked-scenarios)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Changes from the DRF Version](#changes-from-the-drf-version)

## Tech Stack
- **Python 3.12+**
- **Django 5.2 LTS**: models, admin (with Jazzmin), migrations
- **[django-bolt](https://github.com/dj-bolt/django-bolt)**: the API layer. Rust (Actix Web) HTTP server, [msgspec](https://jcristharif.com/msgspec/) request validation and serialization, OpenAPI docs built in
- **[uv](https://docs.astral.sh/uv/)**: dependency and virtual-environment management
- **SQLite** in development, **PostgreSQL** in production (via `DATABASE_URL`)
- **WhiteNoise** for static files

## Project Structure
```
inverter_project/
├── manage.py
├── pyproject.toml / uv.lock      # dependencies (managed by uv)
├── inverter_project/
│   ├── api.py                    # BoltAPI instance: mounts v1/v2 routers, docs, root redirect
│   ├── urls.py                   # Django URLconf (admin only)
│   └── settings/{common,dev,prod}.py
├── api/
│   ├── common/                   # shared by both versions
│   │   ├── appliances.py         # appliance lookup (single query) + listing
│   │   ├── exceptions.py         # UnknownApplianceError (domain error)
│   │   ├── errors.py             # domain error -> 422 response
│   │   ├── sizing.py             # shared sizing model: constants + formulas (pure)
│   │   └── schemas.py            # ApplianceOut
│   ├── v1/
│   │   ├── calculator.py         # pure v1 math (no Django/HTTP imports)
│   │   ├── services.py           # V1CalculationService: resolve appliances, run calculator
│   │   ├── schemas.py            # request/response schemas (msgspec)
│   │   └── routes.py             # HTTP routes: schema -> service -> response
│   ├── v2/                       # same layout as v1, fully independent
│   └── tests/
└── power_calculator/             # Appliance model, admin, populate_appliances command
```

Each version is built in layers:

| Layer | Responsibility | Depends on |
|---|---|---|
| `calculator.py` | Builds the version's energy demand, then applies the shared sizing model. Numbers in, frozen dataclass out | `api/common/sizing.py` |
| `services.py` | Looks up appliances, builds calculator input, returns a result DTO with appliance names | calculator, `api/common` |
| `schemas.py` | Validates and documents HTTP request/response bodies | msgspec |
| `routes.py` | Maps schemas to service DTOs and domain errors to HTTP errors | services, schemas |

v1 and v2 never import from each other. They share only the sizing formulas, which keeps their results consistent. You can add a version (e.g. `v3`) without touching the others.

## Setup

### 1. Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and install dependencies
```bash
git clone https://github.com/JoseSholly/Inverter_power_project.git
cd Inverter_power_project/inverter_project
uv sync            # creates .venv with Python 3.12 and installs everything from uv.lock
```

### 3. Configure environment variables
Create `inverter_project/.env` (python-decouple reads it automatically):
```ini
SECRET_KEY=change-me
# Optional, comma-separated:
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000
# Production only:
# DATABASE_URL=postgres://user:password@host:5432/dbname
```

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | yes | Django secret key |
| `DJANGO_SETTINGS_MODULE` | no | `inverter_project.settings.dev` (default) or `inverter_project.settings.prod`. Set it as a real environment variable, not in `.env`, because it is read before `.env` is loaded |
| `ALLOWED_HOSTS` | no | Extra hosts, added to `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | no | Origins allowed to call the API from a browser |
| `CSRF_TRUSTED_ORIGINS` | no | Origins trusted for CSRF (admin) |
| `DATABASE_URL` | prod only | PostgreSQL connection URL |

### 4. Create the database and load appliances
```bash
uv run python manage.py migrate
uv run python manage.py populate_appliances
uv run python manage.py createsuperuser   # optional, for /admin/
```

### 5. Run the server
```bash
uv run python manage.py runbolt --dev     # auto-reload on code changes
```
The API runs at `http://127.0.0.1:8000/`. Use `--host` and `--port` to change where it binds.

## API Documentation
While the server is running:

| URL | What |
|---|---|
| `/` | Redirects to `/api/docs` |
| `/api/docs` | Swagger UI |
| `/api/docs/redoc` | ReDoc |
| `/api/docs/openapi.json` | Raw OpenAPI schema |
| `/admin/` | Django admin (manage appliances) |

## Endpoints

| Method | Path | Description | Success |
|---|---|---|---|
| GET | `/api/v1/power_calculator/appliances/` | List appliances (`id`, `name`) | 200 |
| POST | `/api/v1/power_calculator/calculate/` | v1 calculation (one backup time) | 200 |
| GET | `/api/v2/power_calculator/appliances/` | List appliances (`id`, `name`) | 200 |
| POST | `/api/v2/power_calculator/calculate/` | v2 calculation (per-appliance backup time) | 200 |

Every path works **with or without the trailing slash** (`/calculate/` and `/calculate` behave the same, with no redirect). The appliance endpoints also answer `HEAD`.

Both appliance endpoints return the same list, newest first:
```json
[
  {"id": 25, "name": "Electric shaver"},
  {"id": 24, "name": "Security Cameras"}
]
```

### Errors
Every error comes back as JSON with a `detail` key. Nothing internal (stack traces, SQL, exception text) is exposed.

| Status | When | Example |
|---|---|---|
| **422** | The body isn't valid JSON, isn't an object, or is empty | `{"detail": [{"type": "json_invalid", "loc": ["body"], "msg": "Input data was truncated", ...}]}` |
| **422** | A field is missing, has the wrong type, or is out of range | see below |
| **422** | An appliance ID doesn't exist | see below |
| **405** | Wrong HTTP method on a known endpoint (e.g. `GET /calculate/`) | `{"detail": "Method not allowed. Allowed methods: OPTIONS, POST."}` with an `Allow` header |
| **404** | Unknown URL | `{"detail": "Not Found"}` |
| **500** | An unexpected server fault (e.g. the database is down) | `{"detail": "Internal Server Error"}` |

Each 422 lists every problem. `loc` is the path to the offending value, and item indexes start at `"0"`:
```json
{
  "detail": [
    {
      "loc": ["body", "items", "0", "quantity"],
      "msg": "Expected `int` <= 1000",
      "type": "validation_error"
    }
  ]
}
```
An appliance ID that isn't in the database gets one error per offending item:
```json
{
  "detail": [
    {
      "type": "unknown_appliance",
      "loc": ["body", "items", "1", "id"],
      "msg": "Appliance with ID 777 does not exist.",
      "input": 777
    }
  ]
}
```

**Logging.** Rejected requests (4xx) are logged as a single WARNING line. Unexpected errors (5xx) are logged at ERROR with the full traceback, so real faults stand out.

**Input limits** keep values realistic for a home system and keep the maths safe from overflow. Values outside these limits get a 422:

| Limit | Value |
|---|---|
| Appliances per request | 1–100 |
| `quantity` | 1–1,000 |
| `power_rating` | up to 100,000 W |
| `backup_time` | up to 24 h (the model recharges from solar once a day) |
| `system_voltage` (v2) | 12–240 V, multiple of 12 |
| `battery_capacity` (v2) | up to 5,000 Ah |
| `solar_panel_watt` (v2) | up to 1,000 W |

## Request Fields

### v1: `POST /api/v1/power_calculator/calculate/`
| Field | Type | Required | Allowed values |
|---|---|---|---|
| `backup_time` | integer | yes | 1–24 (hours; applies to every appliance) |
| `battery_capacity` | integer | yes | `150`, `200`, `220`, `250` (Ah of one 12 V battery) |
| `system_voltage` | integer | yes | `12`, `24`, `48` (V) |
| `solar_panel_watt` | integer | yes | `300`, `350`, `400`, `450` (W of one panel) |
| `items` | array | yes | 1–100 items |
| `items[].id` | integer | yes | an existing appliance ID |
| `items[].quantity` | integer | no (default `1`) | 1–1,000 |
| `items[].power_rating` | integer | no (default `1`) | 1–100,000 (W) |

### v2: `POST /api/v2/power_calculator/calculate/`
| Field | Type | Required | Allowed values |
|---|---|---|---|
| `system_voltage` | number | yes | 12–240, multiple of 12 (V) |
| `battery_capacity` | number | yes | 1–5,000 (Ah of one 12 V battery) |
| `solar_panel_watt` | number | yes | 1–1,000 (Wp of one panel) |
| `items` | array | yes | 1–100 items |
| `items[].id` | integer | yes | an existing appliance ID |
| `items[].quantity` | integer | yes | 1–1,000 |
| `items[].power_rating` | number | yes | 0.01–100,000 (W) |
| `items[].backup_time` | number | yes | 0.01–24 (hours) |

Unknown extra fields are ignored.

## Examples
Ready-to-run scripts are in [`examples/`](examples). They use `requests`, which `uv sync` installs as a dev dependency:
```bash
cd inverter_project
uv run python ../examples/v1_calculation.py
uv run python ../examples/v2_calculation.py
```
The appliance IDs in the examples match a fresh database loaded with `populate_appliances`.

### v1 example
```bash
curl -X POST http://127.0.0.1:8000/api/v1/power_calculator/calculate/ \
  -H "Content-Type: application/json" \
  -d '{
    "backup_time": 4,
    "battery_capacity": 200,
    "system_voltage": 24,
    "solar_panel_watt": 350,
    "items": [
      {"id": 8,  "quantity": 6, "power_rating": 10},
      {"id": 18, "quantity": 3, "power_rating": 75},
      {"id": 17, "quantity": 1, "power_rating": 120},
      {"id": 15, "quantity": 1, "power_rating": 150},
      {"id": 12, "quantity": 2, "power_rating": 150}
    ]
  }'
```
Response `200 OK`:
```json
{
  "total_load": 855,
  "inverter_rating": 1.07,
  "total_battery_capacity": 356.25,
  "numbers_of_batteries": 4,
  "total_solar_panel_capacity_needed": 712.5,
  "numbers_of_solar_panel": 3,
  "total_current": 43.75,
  "controller_current": 54.69,
  "backup_time": 4,
  "battery_capacity": 200,
  "system_voltage": 24,
  "solar_panel_watt": 350,
  "items": [
    {"id": 8,  "name": "LED Light",       "quantity": 6, "power_rating": 10},
    {"id": 18, "name": "Radio",           "quantity": 3, "power_rating": 75},
    {"id": 17, "name": "Home Theater",    "quantity": 1, "power_rating": 120},
    {"id": 15, "name": "Washing Machine", "quantity": 1, "power_rating": 150},
    {"id": 12, "name": "Refrigerator",    "quantity": 2, "power_rating": 150}
  ]
}
```

### v2 example
```bash
curl -X POST http://127.0.0.1:8000/api/v2/power_calculator/calculate/ \
  -H "Content-Type: application/json" \
  -d '{
    "system_voltage": 24.0,
    "battery_capacity": 200.0,
    "solar_panel_watt": 350.0,
    "items": [
      {"id": 1, "quantity": 1, "power_rating": 75.0,  "backup_time": 5.0},
      {"id": 2, "quantity": 1, "power_rating": 120.0, "backup_time": 4.0},
      {"id": 3, "quantity": 8, "power_rating": 7.0,   "backup_time": 7.0}
    ]
  }'
```
Response `200 OK`:
```json
{
  "system_voltage": 24.0,
  "battery_capacity": 200.0,
  "solar_panel_watt": 350.0,
  "total_load": 251.0,
  "inverter_rating": 0.31,
  "total_battery_capacity": 129.9,
  "numbers_of_batteries": 2,
  "total_solar_panel_capacity_needed": 259.79,
  "numbers_of_solar_panel": 1,
  "total_current": 14.58,
  "controller_current": 18.23,
  "items": [
    {"id": 1, "name": "Wifi Router",   "quantity": 1, "power_rating": 75.0,  "backup_time": 5.0},
    {"id": 2, "name": "Phone Charger", "quantity": 1, "power_rating": 120.0, "backup_time": 4.0},
    {"id": 3, "name": "Fridge",        "quantity": 8, "power_rating": 7.0,   "backup_time": 7.0}
  ]
}
```

## Calculation Formulas
Both versions share one sizing model (`api/common/sizing.py`). The **only** difference is how the daily energy demand **E** is built. With the same backup time for every appliance, v1 and v2 give identical results, and a test checks this.

### Constants (both versions)
| Constant | Value | Meaning |
|---|---|---|
| Power factor (PF) | 0.8 | converts W to VA for household loads |
| Inverter efficiency (η<sub>inv</sub>) | 0.8 | inverter and wiring losses (conservative) |
| Depth of discharge (DoD) | 0.5 | usable share of a lead-acid/tubular battery |
| Battery unit voltage | 12 V | batteries are 12 V units wired in series |
| Peak sun hours (PSH) | 6 h | average daily full-sun hours |
| Solar system efficiency (η<sub>sol</sub>) | 0.8 | panel derating, controller and charging losses |
| Controller safety factor | 1.25 | headroom over the array current |

Symbols: **V** = `system_voltage`, **C** = `battery_capacity` (Ah of one battery), **W** = `solar_panel_watt`.
All results are rounded to 2 decimals. Counts are rounded **up**, ignoring float noise such as 3.0000000000000004.

### v1 formulas (one backup time *t* for every appliance)
| # | Output | Formula |
|---|---|---|
| 1 | `total_load` (W) | P = Σ (`power_rating` × `quantity`) |
| 2 | energy (Wh, internal) | **E = P × t** |
| 3 | `inverter_rating` (kVA) | P ÷ PF ÷ 1000 = P ÷ 800 |
| 4 | `total_battery_capacity` (Ah) | Ah = E ÷ (V × η<sub>inv</sub> × DoD) = E ÷ (V × 0.4) |
| 5 | `numbers_of_batteries` | ⌈V ÷ 12⌉ in series × ⌈Ah ÷ C⌉ parallel strings |
| 6 | `total_solar_panel_capacity_needed` (Wp) | Wp = E ÷ (PSH × η<sub>sol</sub>) = E ÷ 4.8 |
| 7 | `numbers_of_solar_panel` | N = ⌈Wp ÷ W⌉ |
| 8 | `total_current` (A) | N × W ÷ V: current of the installed array |
| 9 | `controller_current` (A) | N × W × 1.25 ÷ V: charge controller rating |

### v2 formulas (each appliance *i* has its own backup time *t<sub>i</sub>*)
| # | Output | Formula |
|---|---|---|
| 1 | `total_load` (W) | P = Σ (`power_rating`<sub>i</sub> × `quantity`<sub>i</sub>) |
| 2 | energy (Wh, internal) | **E = Σ (`power_rating`<sub>i</sub> × `quantity`<sub>i</sub> × t<sub>i</sub>)** |
| 3 | `inverter_rating` (kVA) | P ÷ PF ÷ 1000 = P ÷ 800 |
| 4 | `total_battery_capacity` (Ah) | Ah = E ÷ (V × η<sub>inv</sub> × DoD) = E ÷ (V × 0.4) |
| 5 | `numbers_of_batteries` | ⌈V ÷ 12⌉ in series × ⌈Ah ÷ C⌉ parallel strings |
| 6 | `total_solar_panel_capacity_needed` (Wp) | Wp = E ÷ (PSH × η<sub>sol</sub>) = E ÷ 4.8 |
| 7 | `numbers_of_solar_panel` | N = ⌈Wp ÷ W⌉ |
| 8 | `total_current` (A) | N × W ÷ V: current of the installed array |
| 9 | `controller_current` (A) | N × W × 1.25 ÷ V: charge controller rating |

Why these formulas:
- **Inverter** sizes for the peak load running together. It doesn't depend on backup time.
- **Battery Ah** must deliver E through the inverter (÷ 0.8) while only using half the battery's rated capacity (÷ 0.5), which protects lead-acid life.
- **Battery count**: a 24 V bank needs 2 × 12 V batteries in series per string, a 48 V bank needs 4. You add parallel strings until the Ah is covered.
- **Solar** must put back E every day in 6 sun-hours, after 20% losses.
- **Currents** are based on the panels actually installed (N × W), because that is what the controller has to handle.

## Worked Scenarios
The same home is sized with both versions. Appliance IDs match a fresh database loaded with `populate_appliances`.

**The home**: 4 LED bulbs (10 W), 2 fans (75 W), a TV (120 W), a fridge (150 W) and a laptop (65 W), on a **24 V** system with **200 Ah** batteries and **400 W** panels.

### Scenario 1 (v1): 6 hours of backup for everything
Request:
```json
{
  "backup_time": 6,
  "battery_capacity": 200,
  "system_voltage": 24,
  "solar_panel_watt": 400,
  "items": [
    {"id": 8,  "quantity": 4, "power_rating": 10},
    {"id": 9,  "quantity": 2, "power_rating": 75},
    {"id": 4,  "quantity": 1, "power_rating": 120},
    {"id": 3,  "quantity": 1, "power_rating": 150},
    {"id": 11, "quantity": 1, "power_rating": 65}
  ]
}
```
Step by step:

| Step | Working | Result |
|---|---|---|
| Load P | 4×10 + 2×75 + 120 + 150 + 65 | **525 W** |
| Energy E | 525 W × 6 h | 3,150 Wh |
| Inverter | 525 ÷ 800 = 0.656 | **0.66 kVA** (buy a 1 kVA unit) |
| Battery Ah | 3,150 ÷ (24 × 0.4) = 328.125 | **328.12 Ah** |
| Batteries | ⌈24 ÷ 12⌉ = 2 in series × ⌈328.12 ÷ 200⌉ = 2 strings | **4 batteries** (2S2P) |
| Solar Wp | 3,150 ÷ 4.8 | **656.25 Wp** |
| Panels | ⌈656.25 ÷ 400⌉ | **2 panels** (800 W installed) |
| Array current | 2 × 400 ÷ 24 | **33.33 A** |
| Controller | 33.33 × 1.25 | **41.67 A** (buy a 50 A controller) |

Response `200 OK` (items abbreviated):
```json
{
  "total_load": 525,
  "inverter_rating": 0.66,
  "total_battery_capacity": 328.12,
  "numbers_of_batteries": 4,
  "total_solar_panel_capacity_needed": 656.25,
  "numbers_of_solar_panel": 2,
  "total_current": 33.33,
  "controller_current": 41.67,
  "backup_time": 6,
  "battery_capacity": 200,
  "system_voltage": 24,
  "solar_panel_watt": 400,
  "items": [{"id": 8, "name": "LED Light", "quantity": 4, "power_rating": 10}, "..."]
}
```

### Scenario 2 (v2): each appliance runs as long as it's really needed
The same home, but the fridge runs all night while the TV runs only in the evening:

| Appliance | Power × qty | Backup | Energy |
|---|---|---|---|
| LED Light (id 8) | 10 W × 4 | 8 h | 320 Wh |
| Fan (id 9) | 75 W × 2 | 6 h | 900 Wh |
| TV (id 4) | 120 W × 1 | 3 h | 360 Wh |
| Fridge (id 3) | 150 W × 1 | 10 h | 1,500 Wh |
| Laptop (id 11) | 65 W × 1 | 4 h | 260 Wh |
| **Total** | **525 W** | | **3,340 Wh** |

Request:
```json
{
  "system_voltage": 24,
  "battery_capacity": 200,
  "solar_panel_watt": 400,
  "items": [
    {"id": 8,  "quantity": 4, "power_rating": 10,  "backup_time": 8},
    {"id": 9,  "quantity": 2, "power_rating": 75,  "backup_time": 6},
    {"id": 4,  "quantity": 1, "power_rating": 120, "backup_time": 3},
    {"id": 3,  "quantity": 1, "power_rating": 150, "backup_time": 10},
    {"id": 11, "quantity": 1, "power_rating": 65,  "backup_time": 4}
  ]
}
```
Step by step:

| Step | Working | Result |
|---|---|---|
| Load P | same appliances | **525 W** |
| Energy E | sum of the energy column | 3,340 Wh |
| Inverter | 525 ÷ 800 | **0.66 kVA** (unchanged: backup time doesn't affect it) |
| Battery Ah | 3,340 ÷ (24 × 0.4) = 347.92 | **347.92 Ah** |
| Batteries | 2 in series × ⌈347.92 ÷ 200⌉ = 2 strings | **4 batteries** (2S2P) |
| Solar Wp | 3,340 ÷ 4.8 | **695.83 Wp** |
| Panels | ⌈695.83 ÷ 400⌉ | **2 panels** (800 W installed) |
| Array current | 2 × 400 ÷ 24 | **33.33 A** |
| Controller | 33.33 × 1.25 | **41.67 A** |

Response `200 OK` (items abbreviated):
```json
{
  "system_voltage": 24.0,
  "battery_capacity": 200.0,
  "solar_panel_watt": 400.0,
  "total_load": 525.0,
  "inverter_rating": 0.66,
  "total_battery_capacity": 347.92,
  "numbers_of_batteries": 4,
  "total_solar_panel_capacity_needed": 695.83,
  "numbers_of_solar_panel": 2,
  "total_current": 33.33,
  "controller_current": 41.67,
  "items": [{"id": 8, "name": "LED Light", "quantity": 4, "power_rating": 10.0, "backup_time": 8.0}, "..."]
}
```

### Comparing the two
- The **load and inverter are the same**. Only energy-based outputs (battery Ah, solar Wp) change.
- v2 needs **190 Wh more** energy here, because the fridge's 10 h outweighs the TV's shorter 3 h. Both still fit in 4 batteries and 2 panels.
- Use **v1** for a quick estimate when everything should last the same time. Use **v2** when appliances run for different lengths of time, which gives a tighter, more realistic size.
- If you give every v2 item the same backup time as v1 (6 h), v2 returns exactly the v1 numbers.

## Running Tests
```bash
cd inverter_project
uv run python manage.py test
```
The suite covers each version's calculator (pure unit tests), each service (with the database) and the HTTP endpoints (through django-bolt's `TestClient`).

## Deployment
- Use **Python 3.12+** on the host.
- Install: `uv sync --frozen --no-dev`. If your platform needs a `requirements.txt`, generate one with `uv export --no-dev --frozen -o requirements.txt`.
- Set `DJANGO_SETTINGS_MODULE=inverter_project.settings.prod`, `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`.
- Build step:
  ```bash
  uv run python manage.py collectstatic --noinput
  uv run python manage.py migrate
  ```
- Start command (bind to the port your platform provides):
  ```bash
  uv run python manage.py runbolt --host 0.0.0.0 --port $PORT --processes 2
  ```
  `runbolt` serves the API, the docs, the admin and static files. You don't need gunicorn or uvicorn.

## Changes from the DRF Version
- The API runs on **django-bolt** instead of Django REST Framework. Request and response bodies are the same shape as before.
- Validation errors return **422** in the format above (DRF returned 400 with a different body).
- v1 `calculate` returns **200** instead of 201, because nothing is created.
- **Battery count fix (v1 and v2)**: the count is now batteries in series × parallel strings. Previously v1 returned only `V / 12` for 24/48 V systems whatever the load, and v2 ignored the series count.
- v1 `inverter_rating` is rounded to 2 decimals, like v2.
- **One sizing model for both versions.** Battery capacity now allows for inverter losses (0.8) and a 50% depth of discharge, so the bank is no longer undersized. Before, v2 had neither and v1 had only the inverter factor. Solar is rounded once, at the end. Both versions return `total_current` (installed array) and `controller_current` (array × 1.25). Before, v2 sized the controller from the required capacity instead of the installed panels.
- v2 `system_voltage` must be a multiple of 12 V, because batteries are 12 V units.
- `items` must contain 1–100 appliances, and every numeric input has a realistic upper limit. Absurd values used to crash the server (500) or return nonsense.
- The wrong HTTP method still returns **405** with an `Allow` header, as with DRF. Paths now also work **without the trailing slash**: DRF redirected them (301), and a POST was then lost.
- The unknown-appliance error points at the exact item (`loc: ["body", "items", "<index>", "id"]`).
- API docs moved to `/api/docs`. Dependencies are managed with uv. Python 3.12+ and Django 5.2 are required.
