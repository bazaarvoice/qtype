# Extending QType CLI

QType supports third-party CLI plugins through Python entry points. This allows developers to extend the QType CLI with custom commands without modifying the core codebase.

## Creating a Plugin

### 1. Define Your Command Function

Create a module with a parser function that takes a subparsers object and registers your command:

```python
# my_package/qtype_commands.py
import argparse

def my_command_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'my-command' subcommand."""
    parser = subparsers.add_parser(
        'my-command',
        help='My custom QType command'
    )
    parser.add_argument(
        '--option',
        help='An example option'
    )
    # Set the function to call when this command is invoked
    parser.set_defaults(func=my_command_handler)

def my_command_handler(args: argparse.Namespace) -> None:
    """Handle the 'my-command' subcommand."""
    print(f"Running my-command with option: {args.option}")
```

### 2. Register the Entry Point

Add the entry point to your package's `pyproject.toml`:

```toml
[project.entry-points."qtype.commands"]
my-command = "my_package.qtype_commands:my_command_parser"
```

Or if using `setup.py`:

```python
from setuptools import setup

setup(
    name="my-qtype-plugin",
    # ... other setup parameters
    entry_points={
        "qtype.commands": [
            "my-command = my_package.qtype_commands:my_command_parser",
        ],
    },
)
```

### 3. Install and Test

After installing your package, the command will be automatically available:

```bash
pip install my-qtype-plugin
qtype my-command --option "test"
```

## Best Practices

1. **Naming**: Use descriptive command names and avoid conflicts with built-in commands
2. **Error Handling**: Handle errors gracefully and provide helpful error messages
3. **Documentation**: Include help text for your commands and arguments
4. **Dependencies**: Declare any additional dependencies your plugin requires
5. **Testing**: Test your plugin with different versions of QType

## Debugging Plugins

To see debug information about plugin loading, run QType with debug logging:

```bash
qtype --log-level DEBUG my-command
```

This will show which plugins are being loaded and any errors that occur during the loading process.

## Example Plugin Structure

```
my-qtype-plugin/
├── pyproject.toml
├── my_package/
│   ├── __init__.py
│   └── qtype_commands.py
└── tests/
    └── test_plugin.py
```
