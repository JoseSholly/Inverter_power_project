"""Route registration helpers shared by every API version.

django-bolt's router has two behaviours we don't want for this API:
- a path with no trailing slash gets a 308 redirect, which some clients
  won't follow for a POST;
- a known path called with the wrong HTTP method returns 404 instead of 405.

`Routes` registers each endpoint at both `/path/` and `/path` (only the
slash form appears in the OpenAPI docs). `finalize()` then adds a 405
handler, with an `Allow` header, for every other method on those paths.
"""
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from django_bolt import Router
from django_bolt.exceptions import MethodNotAllowed

HANDLED_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE")
"""OPTIONS is left to Bolt's CORS preflight handling, so it never gets a 405 handler."""


def _path_variants(path: str) -> tuple[str, ...]:
    bare = path.rstrip("/")
    return (path,) if bare == path or not bare else (path, bare)


def _method_not_allowed_handler(allow: str) -> Callable[[], Any]:
    async def method_not_allowed():
        raise MethodNotAllowed(
            detail=f"Method not allowed. Allowed methods: {allow}.",
            headers={"Allow": allow},
        )

    return method_not_allowed


class Routes:
    def __init__(self, router: Router):
        self.router = router
        self._allowed: dict[str, set[str]] = defaultdict(set)

    def get(self, path: str, **kwargs: Any):
        """GET endpoint; HEAD is served by the same handler (Bolt doesn't add it)."""

        def decorator(handler):
            self._route("GET", path, **kwargs)(handler)
            head_kwargs = {k: v for k, v in kwargs.items() if k != "name"}
            self._route("HEAD", path, **head_kwargs, include_in_schema=False)(handler)
            return handler

        return decorator

    def post(self, path: str, **kwargs: Any):
        return self._route("POST", path, **kwargs)

    def _route(self, method: str, path: str, **kwargs: Any):
        def decorator(handler):
            register = getattr(self.router, method.lower())
            primary, *aliases = _path_variants(path)
            register(primary, **kwargs)(handler)
            alias_kwargs = {k: v for k, v in kwargs.items() if k not in ("name", "include_in_schema")}
            for alias in aliases:
                register(alias, **alias_kwargs, include_in_schema=False)(handler)
            self._allowed[path].add(method)
            return handler

        return decorator

    def finalize(self) -> Router:
        """Register 405 handlers for unsupported methods; call after all routes."""
        for path, methods in self._allowed.items():
            allowed = set(methods) | {"OPTIONS"}
            allow = ", ".join(sorted(allowed))
            for method in HANDLED_METHODS:
                if method in methods:
                    continue
                register = getattr(self.router, method.lower())
                for variant in _path_variants(path):
                    register(variant, include_in_schema=False)(_method_not_allowed_handler(allow))
        return self.router
