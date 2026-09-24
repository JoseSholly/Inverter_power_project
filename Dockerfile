FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    DJANGO_SETTINGS_MODULE=inverter_project.settings.prod \
    PATH="/app/inverter_project/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv==0.5.14

COPY inverter_project/pyproject.toml inverter_project/uv.lock ./inverter_project/
WORKDIR /app/inverter_project
RUN uv sync --frozen --no-dev

COPY inverter_project/ ./

RUN SECRET_KEY=build-only \
    DATABASE_URL=sqlite:///build.db \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py populate_appliances -v 0 && python manage.py runbolt --host 0.0.0.0 --port ${PORT:-8000}"]
