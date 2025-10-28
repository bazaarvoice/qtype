"""
Command-line interface for visualizing QType YAML spec files.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import tempfile
import webbrowser
from pathlib import Path
from typing import Any

from qtype.base.exceptions import LoadError, ValidationError
from qtype.semantic.loader import load
from qtype.semantic.model import Application
from qtype.semantic.visualize import visualize_application

logger = logging.getLogger(__name__)


def main(args: Any) -> None:
    """
    Visualize a QType YAML spec file.

    Args:
        args: Arguments passed from the command line or calling context.

    Exits:
        Exits with code 1 if visualization fails.
    """
    spec_path = Path(args.spec)

    try:
        # Load and generate visualization
        semantic_model, _ = load(spec_path)
        assert isinstance(semantic_model, Application)
        mermaid_content = visualize_application(semantic_model)

        if args.output:
            # Write to file
            output_path = Path(args.output)
            output_path.write_text(mermaid_content, encoding="utf-8")
            logger.info(f"✅ Visualization saved to {output_path}")

        if not args.no_display:
            # Check if mmdc is available
            if shutil.which("mmdc") is None:
                logger.error(
                    "❌ mmdc command not found. Please install mermaid-cli."
                )
                logger.info(
                    "Install with: npm install -g @mermaid-js/mermaid-cli"
                )
                exit(1)

            # Create temporary directory and run mmdc from within it
            try:
                # Create a temporary directory
                temp_dir = tempfile.mkdtemp()
                temp_dir_path = Path(temp_dir)

                # Write mermaid file with simple names in the temp directory
                mmd_file_path = temp_dir_path / "diagram.mmd"
                svg_file_path = temp_dir_path / "diagram.svg"

                mmd_file_path.write_text(mermaid_content, encoding="utf-8")

                # Run mmdc from within the temporary directory
                subprocess.run(
                    ["mmdc", "-i", "diagram.mmd", "-o", "diagram.svg"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )

                logger.info(
                    f"Opening visualization in browser: {svg_file_path}"
                )
                webbrowser.open(f"file://{svg_file_path}")

            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to generate SVG: {e.stderr}")
                exit(1)

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
