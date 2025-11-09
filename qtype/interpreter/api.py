from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from opentelemetry import trace

from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.base.secrets import create_secret_manager
from qtype.interpreter.endpoints import (
    create_rest_endpoint,
    create_streaming_endpoint,
)
from qtype.interpreter.metadata_api import create_metadata_endpoints
from qtype.semantic.model import Application


class APIExecutor:
    """API executor for QType definitions with dynamic endpoint generation."""

    def __init__(
        self,
        definition: Application,
        host: str = "localhost",
        port: int = 8000,
    ):
        self.definition = definition
        self.host = host
        self.port = port

    def create_app(
        self,
        name: str | None = None,
        ui_enabled: bool = True,
        fast_api_args: dict | None = None,
        servers: list[dict] | None = None,
    ) -> FastAPI:
        """Create FastAPI app with dynamic endpoints."""
        if fast_api_args is None:
            fast_api_args = {
                "docs_url": "/docs",
                "redoc_url": "/redoc",
            }

        # Add servers to FastAPI kwargs if provided
        if servers is not None:
            fast_api_args["servers"] = servers

        # Create secret manager if configured
        secret_manager = create_secret_manager(self.definition.secret_manager)

        # Create lifespan context manager for telemetry
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Manage telemetry lifecycle during app startup/shutdown."""
            tracer_provider = None
            if self.definition.telemetry:
                from qtype.interpreter.telemetry import register

                tracer_provider = register(
                    self.definition.telemetry,
                    project_id=name or self.definition.id,
                    secret_manager=secret_manager,
                )
            yield
            # Fire off telemetry shutdown in background for fast reloads
            if tracer_provider is not None:

                async def shutdown_telemetry():
                    tracer_provider.force_flush(timeout_millis=1000)
                    tracer_provider.shutdown()

                asyncio.create_task(shutdown_telemetry())

        # Create FastAPI app with lifespan
        app = FastAPI(
            title=name or "QType API", lifespan=lifespan, **fast_api_args
        )

        # Serve static UI files if they exist
        if ui_enabled:
            # Add CORS middleware only for localhost development
            if self.host in ("localhost", "127.0.0.1", "0.0.0.0"):
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            ui_dir = Path(__file__).parent / "ui"
            if ui_dir.exists():
                app.mount(
                    "/ui",
                    StaticFiles(directory=str(ui_dir), html=True),
                    name="ui",
                )
                app.get("/", include_in_schema=False)(
                    lambda: RedirectResponse(url="/ui")
                )

        # Create metadata endpoints for flow discovery
        create_metadata_endpoints(app, self.definition)

        # Create executor context
        context = ExecutorContext(
            secret_manager=secret_manager,
            tracer=trace.get_tracer(__name__),
        )

        # Create unified invoke endpoints for each flow
        flows = self.definition.flows if self.definition.flows else []
        for flow in flows:
            if flow.interface is not None:
                create_streaming_endpoint(app, flow, context)
            create_rest_endpoint(app, flow, context)

        return app
