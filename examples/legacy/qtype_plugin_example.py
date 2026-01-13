"""
Example QType CLI plugin.

This demonstrates how to create a third-party plugin for the QType CLI.
To use this as a plugin, you would:

1. Put this code in a separate package
2. Add an entry point in pyproject.toml:
   [project.entry-points."qtype.commands"]
   example = "your_package.qtype_example:parser"
3. Install the package
"""

import argparse


def parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'example' subcommand.

    Args:
        subparsers: The subparsers object to add the command to.
    """
    example_parser = subparsers.add_parser(
        "example", help="Example plugin command for QType CLI"
    )
    example_parser.add_argument(
        "--message",
        default="Hello from QType plugin!",
        help="Message to display (default: Hello from QType plugin!)",
    )
    example_parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of times to display the message (default: 1)",
    )
    # Set the function to call when this command is invoked
    example_parser.set_defaults(func=example_command)


def example_command(args: argparse.Namespace) -> None:
    """Handle the 'example' subcommand.

    Args:
        args: Command-line arguments containing message and count.
    """
    for i in range(args.count):
        print(f"{i + 1}: {args.message}")

    print("\nThis command was loaded as a plugin!")
    print("Plugin authors can extend QType CLI functionality this way.")
