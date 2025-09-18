"""
Command-line interface for visualizing QType YAML spec files.
"""

from __future__ import annotations

import argparse
import logging
import tempfile
import webbrowser
from pathlib import Path
from typing import Any

from qtype.application.facade import QTypeFacade
from qtype.base.exceptions import LoadError, ValidationError

logger = logging.getLogger(__name__)


def main(args: Any) -> None:
    """
    Visualize a QType YAML spec file.

    Args:
        args: Arguments passed from the command line or calling context.

    Exits:
        Exits with code 1 if visualization fails.
    """
    facade = QTypeFacade()
    spec_path = Path(args.spec)

    try:
        # Generate visualization using the facade
        mermaid_content = facade.visualize_application(spec_path)

        if args.output:
            # Write to file
            output_path = Path(args.output)
            output_path.write_text(mermaid_content, encoding="utf-8")
            logger.info(f"✅ Visualization saved to {output_path}")

        if not args.no_display:
            # Create temporary HTML file and open in browser
            try:
                import mermaid as md  # type: ignore[import-untyped]

                mm = md.Mermaid(mermaid_content)
                html_content = mm._repr_html_()

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".html", delete=False, encoding="utf-8"
                ) as f:
                    f.write(html_content)
                    temp_file = f.name

                logger.info(f"Opening visualization in browser: {temp_file}")
                webbrowser.open(f"file://{temp_file}")
            except ImportError:
                logger.warning(
                    "❌ Mermaid library not installed. Cannot display in browser."
                )
                logger.info("Install with: pip install mermaid")

    except LoadError as e:
        logger.error(f"❌ Failed to load document: {e}")
        exit(1)
    except ValidationError as e:
        logger.error(f"❌ Visualization failed: {e}")
        exit(1)


def parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the visualize subcommand parser.

    Args:
        subparsers: The subparsers object to add the command to.
    """
    cmd_parser = subparsers.add_parser(
        "visualize", help="Visualize a QType Application."
    )
    cmd_parser.add_argument(
        "spec", type=str, help="Path to the QType YAML file."
    )
    cmd_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="If provided, write the mermaid diagram to this file.",
    )
    cmd_parser.add_argument(
        "-nd",
        "--no-display",
        action="store_true",
        help="If set don't display the diagram in a browser (default: False).",
    )
    cmd_parser.set_defaults(func=main)
