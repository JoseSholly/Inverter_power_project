"""django-bolt entry point. Served by `python manage.py runbolt`."""

from django_bolt import BoltAPI
from django_bolt.logging import LoggingConfig
from django_bolt.openapi import (
    JsonRenderPlugin,
    OpenAPIConfig,
    RedocRenderPlugin,
    SwaggerRenderPlugin,
)
from django_bolt.responses import Redirect

from api.common.logging import log_exception
from api.v1.routes import router as v1_router
from api.v2.routes import router as v2_router

DOCS_PATH = "/api/docs"

api = BoltAPI(
    trailing_slash="keep",
    logging_config=LoggingConfig(exception_logging_handler=log_exception),
    openapi_config=OpenAPIConfig(
        title="Home Inverter Calculator API",
        version="2.0.0",
        description="Size an inverter, battery bank and solar array from a list of appliances.",
        path=DOCS_PATH,
        render_plugins=[
            SwaggerRenderPlugin(path="/"),
            RedocRenderPlugin(path="/redoc"),
            JsonRenderPlugin(path="/openapi.json"),
        ],
    ),
)


@api.get("/", include_in_schema=False)
def root():
    return Redirect(DOCS_PATH, status_code=302)


api.include_router(v1_router, prefix="/api/v1/power_calculator")
api.include_router(v2_router, prefix="/api/v2/power_calculator")

# runbolt mounts the Django admin (/admin/) automatically.
