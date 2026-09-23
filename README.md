# Inverter Power Project API

A stateless API that sizes a home backup power system. You send a list of appliances and get back the inverter rating, battery bank, solar array and charge current you need. Nothing is saved: each request is calculated and returned straight away.

There are two versions of the calculation:

- **v1** uses **one backup time for all appliances** and only accepts standard component sizes (12/24/48 V systems, 150–250 Ah batteries, 300–450 W panels).
- **v2** lets **each appliance have its own backup time** and accepts any positive system voltage, battery capacity and panel wattage.

## Table of Contents
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [API Documentation](#api-documentation)
- [Endpoints](#endpoints)
- [Request Fields](#request-fields)
- [Examples](#examples)
- [Calculation Formulas](#calculation-formulas)
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
| `calculator.py` | Sizing math only. Numbers in, frozen dataclass out | nothing |
| `services.py` | Looks up appliances, builds calculator input, returns a result DTO with appliance names | calculator, `api/common` |
| `schemas.py` | Validates and documents HTTP request/response bodies | msgspec |
| `routes.py` | Maps schemas to service DTOs and domain errors to HTTP errors | services, schemas |

v1 and v2 never import from each other, so you can change or add a version (e.g. `v3`) without touching the others.

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

Both appliance endpoints return the same list, newest first:
```json
[
  {"id": 25, "name": "Electric shaver"},
  {"id": 24, "name": "Security Cameras"}
]
```

### Errors
Invalid input returns **422 Unprocessable Entity** with a list of problems. `loc` points to the field that failed:
```json
{
  "detail": [
    {
      "loc": ["body", "battery_capacity"],
      "msg": "Invalid enum value 123",
      "type": "validation_error"
    }
  ]
}
```
An appliance ID that isn't in the database also returns 422:
```json
{
  "detail": [
    {
      "type": "unknown_appliance",
      "loc": ["body", "items", "id"],
      "msg": "Appliance(s) with ID 999 do not exist in the database.",
      "input": [999]
    }
  ]
}
```

## Request Fields

### v1: `POST /api/v1/power_calculator/calculate/`
| Field | Type | Required | Allowed values |
|---|---|---|---|
| `backup_time` | integer | yes | ≥ 1 (hours; applies to every appliance) |
| `battery_capacity` | integer | yes | `150`, `200`, `220`, `250` (Ah of one 12 V battery) |
| `system_voltage` | integer | yes | `12`, `24`, `48` (V) |
| `solar_panel_watt` | integer | yes | `300`, `350`, `400`, `450` (W of one panel) |
| `items` | array | yes | at least 1 item |
| `items[].id` | integer | yes | an existing appliance ID |
| `items[].quantity` | integer | no (default `1`) | ≥ 1 |
| `items[].power_rating` | integer | no (default `1`) | ≥ 1 (W) |

### v2: `POST /api/v2/power_calculator/calculate/`
| Field | Type | Required | Allowed values |
|---|---|---|---|
| `system_voltage` | number | yes | ≥ 1 (V) |
| `battery_capacity` | number | yes | ≥ 1 (Ah of one 12 V battery) |
| `solar_panel_watt` | number | yes | ≥ 1 (Wp of one panel) |
| `items` | array | yes | at least 1 item |
| `items[].id` | integer | yes | an existing appliance ID |
| `items[].quantity` | integer | yes | ≥ 1 |
| `items[].power_rating` | number | yes | ≥ 0.01 (W) |
| `items[].backup_time` | number | yes | ≥ 0.01 (hours) |

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
  "total_battery_capacity": 178.12,
  "numbers_of_batteries": 2,
  "total_solar_panel_capacity_needed": 712.5,
  "numbers_of_solar_panel": 3,
  "total_current": 43.75,
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
  "total_battery_capacity": 51.96,
  "numbers_of_batteries": 2,
  "total_solar_panel_capacity_needed": 259.79,
  "numbers_of_solar_panel": 1,
  "controller_current": 13.53,
  "items": [
    {"id": 1, "name": "Wifi Router",   "quantity": 1, "power_rating": 75.0,  "backup_time": 5.0},
    {"id": 2, "name": "Phone Charger", "quantity": 1, "power_rating": 120.0, "backup_time": 4.0},
    {"id": 3, "name": "Fridge",        "quantity": 8, "power_rating": 7.0,   "backup_time": 7.0}
  ]
}
```

## Calculation Formulas
Symbols: *P* = Σ(power_rating × quantity) in W, *t* = backup time (h), *V* = system voltage, *C* = capacity of one battery (Ah), *W* = watts of one panel.

Batteries are treated as **12 V units**. A bank needs `ceil(V / 12)` batteries in series per string and `ceil(required Ah / C)` strings in parallel:

`numbers_of_batteries = ceil(V / 12) × ceil(total_battery_capacity / C)`

### v1 (`api/v1/calculator.py`)
Constants: power factor 0.8, inverter efficiency 0.8, 6 peak sun hours.

| Output | Formula |
|---|---|
| `total_load` (W) | *P* |
| `inverter_rating` (kVA) | round(*P* / 0.8 / 1000, 2) |
| `total_battery_capacity` (Ah) | round(*P* × *t* / (*V* × 0.8), 2) |
| `numbers_of_batteries` | series × parallel (see above) |
| `total_solar_panel_capacity_needed` (W) | round(*P* × *t* / 6) / 0.8 |
| `numbers_of_solar_panel` | ceil(solar capacity / *W*) |
| `total_current` (A) | round(panels × *W* / *V*, 2) |

### v2 (`api/v2/calculator.py`)
Constants: power factor 0.8, system loss factor 0.8, 6 peak sun hours, 1.25 controller safety factor.
Energy *E* = Σ(power_rating × quantity × backup_time) in Wh, so each appliance uses its own backup time.

| Output | Formula |
|---|---|
| `total_load` (W) | round(*P*, 2) |
| `inverter_rating` (kVA) | round(*P* / 0.8 / 1000, 2) |
| `total_battery_capacity` (Ah) | round(*E* / *V*, 2) |
| `numbers_of_batteries` | series × parallel (see above) |
| `total_solar_panel_capacity_needed` (Wp) | round(*E* / 0.8 / 6, 2) |
| `numbers_of_solar_panel` | ceil(solar capacity / *W*) |
| `controller_current` (A) | round(solar capacity × 1.25 / *V*, 2) |

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
- `items` must contain at least one appliance.
- API docs moved to `/api/docs`. Dependencies are managed with uv. Python 3.12+ and Django 5.2 are required.
