from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from qtype.dsl.base_types import StepCardinality
from qtype.interpreter.batch.flow import batch_execute_flow
from qtype.interpreter.batch.types import BatchConfig, ErrorMode
from qtype.interpreter.flow import execute_flow
from qtype.interpreter.typing import (
    create_input_type_model,
    create_output_type_model,
)
from qtype.semantic.model import Application, Flow


from qtype.interpreter.rest.rest_api import (
    create_rest_flow_endpoint,
)
from qtype.interpreter.stream.stream_api import (
    create_stream_flow_endpoint
)

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
                app.get("/")(lambda: RedirectResponse(url="/ui"))

        flows = self.definition.flows if self.definition.flows else []

        # Dynamically generate POST endpoints for each flow
        for flow in flows:
            if flow.mode == "Chat":
                from qtype.interpreter.stream.chat.chat_api import (
                    create_chat_flow_endpoint,
                )

                create_chat_flow_endpoint(app, flow)
            else:
                create_stream_flow_endpoint(app, flow)
                create_rest_flow_endpoint(app, flow)
        return app
