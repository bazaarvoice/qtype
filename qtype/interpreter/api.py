from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

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

        app = FastAPI(title=name or "QType API", **fast_api_args)

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

        # Create unified invoke endpoints for each flow
        flows = self.definition.flows if self.definition.flows else []
        for flow in flows:
            if flow.interface is not None:
                create_streaming_endpoint(app, flow)
            create_rest_endpoint(app, flow)

        return app
