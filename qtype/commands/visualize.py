"""
Command-line interface for visualizing QType YAML spec files.
"""

import argparse
import logging
import tempfile
import webbrowser
from typing import Any

from qtype.loader import load
from qtype.semantic.visualize import visualize_application

logger = logging.getLogger(__name__)


def main(args: Any) -> None:
    """
    visualize a QType YAML spec file against the QTypeSpec schema and semantics.

    Args:
        args: Arguments passed from the command line or calling context.

    Exits:
        Exits with code 1 if validation fails.
    """
    import mermaid as md

    application = load(args.spec)

    diagram = visualize_application(application)

    if args.output:
        if args.output.endswith(".mmd") or args.output.endswith(".mermaid"):
            with open(args.output, "w") as f:
                f.write(diagram)
            logger.info(f"Mermaid diagram written to {args.output}")
            render = None
        elif args.output.endswith(".svg"):
            render = md.Mermaid(diagram)
            render.to_svg(args.output)
            logger.info(f"SVG diagram written to {args.output}")

        elif args.output.endswith(".png"):
            render = md.Mermaid(diagram)
            render.to_png(args.output)
            logger.info(f"PNG diagram written to {args.output}")

    if not args.no_display:
        if not render:
            render = md.Mermaid(diagram)

        html_content = render._repr_html_()
        # Create a temporary HTML file to display the diagram
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".html"
        ) as temp_file:
            temp_file.write(html_content.encode("utf-8"))
            webbrowser.open(temp_file.name)


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
