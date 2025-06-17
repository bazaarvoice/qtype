# Contributing to QType

Welcome to the QType development guide! This document provides comprehensive instructions for setting up your development environment and contributing to the project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Environment Setup](#development-environment-setup)
- [Installing QType for Development](#installing-qtype-for-development)
- [Running Tests](#running-tests)
- [Code Quality and Standards](#code-quality-and-standards)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [CLI Usage](#cli-usage)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Python 3.9 or higher** (this project targets Python 3.9+)
- **uv** package manager (recommended) or **pip**
- **Git** for version control

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/qtype.git
cd qtype
```

### 2. Set Up Python Environment

We recommend using `uv` for dependency management as it's faster and more reliable:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies including development tools
uv sync --group dev
```

## Installing QType for Development

Install QType in editable mode so changes to the source code are immediately reflected:

```bash
# Install in development mode
uv pip install -e .

# Or if you want to install with specific development dependencies
uv pip install -e ".[dev]"  # If dev extras are defined in pyproject.toml
```

After installation, you should be able to run the `qtype` command from anywhere:

```bash
qtype --help
```

## Running Tests

The project uses Python's built-in unittest framework with coverage measurement:

```bash
# Run all tests with coverage
uv run coverage run -m unittest discover tests/

# View coverage report in terminal
uv run coverage report

# View detailed coverage with missing lines
uv run coverage report --show-missing

# Generate HTML coverage report
uv run coverage html
# Open htmlcov/index.html in your browser to see detailed coverage

# Run specific test file with coverage
uv run coverage run -m unittest tests.test_semantic_validation
uv run coverage report

# Run specific test class
uv run coverage run -m unittest tests.test_semantic_validation.TestUniqueIDs
uv run coverage report

# Run specific test method
uv run coverage run -m unittest tests.test_semantic_validation.TestUniqueIDs.test_unique_model_ids
uv run coverage report

# Run with verbose unittest output
uv run coverage run -m unittest discover tests/ -v
uv run coverage report
```

### Coverage Reports

Coverage reports show:
- Which lines of code are executed during tests
- Which lines are missing test coverage  
- Overall coverage percentage for each module
- HTML report with line-by-line coverage highlighting

The HTML coverage report (`htmlcov/index.html`) provides the most detailed view, showing exactly which lines need more test coverage.

## Code Quality and Standards

This project follows strict Python coding standards:

### Code Style Requirements

- **PEP 8** compliance for all Python code
- **Type hints** for all function signatures and class attributes
- **Docstrings** for all public functions, classes, and modules
- **Clear naming** using snake_case for functions/variables, PascalCase for classes
- **Line length** limit of 79 characters (as per PEP 8)
- **f-strings** for string interpolation
- **Explicit over implicit** code style

#### Format code automatically:

```bash
# Format with ruff
ruff format qtype/ tests/

# Lint with ruff
ruff check qtype/ tests/

# Sort imports
isort qtype/ tests/

# Type checking with mypy
mypy qtype/
```

#### Pre-commit hooks (Optional but recommended):

```bash
uv pip install pre-commit
pre-commit install
```

Settings are in `.pre-commit-config.yaml`:


## Project Structure

```
qtype/
├── pyproject.toml          # Project configuration and dependencies
├── uv.lock                 # Locked dependency versions
├── README.md               # Project overview
├── CONTRIBUTING.md         # This file
├── LICENSE                 # Project license
├── qtype/                  # Main package
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── commands/           # CLI command implementations
│   │   ├── generate_schema.py
│   │   └── validate.py
│   ├── dsl/                # Domain-specific language models
│   │   ├── models.py       # Pydantic models for DSL
│   │   └── validator.py    # DSL validation logic
│   ├── ir/                 # Intermediate representation
│   │   ├── models.py       # IR models
│   │   ├── resolver.py     # IR resolution logic
│   │   └── validator.py    # IR validation logic
│   ├── parser/             # YAML parsing
│   │   └── loader.py
│   ├── generator/          # Code generation
│   │   └── llama_index_gen.py
│   └── utils/              # Utilities
│       └── telemetry.py
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_loader.py
│   └── test_ir_resolution.py
├── docs/                   # Documentation
├── examples/               # Example QType specifications
└── schema/                 # Generated JSON schemas
```

## Making Changes

### Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Write or update tests** for your changes

4. **Run tests** to ensure nothing is broken:
   ```bash
   coverage run -m unittest discover tests/
   ```

5. **Check code quality:**
   ```bash
   ruff format qtype/ tests/
   ruff check qtype/ tests/
   isort qtype/ tests/
   mypy qtype/
   ```

6. **Test CLI functionality:**
   ```bash
   # Generate schema
   qtype generate-schema -o schema/test.json
   
   # Validate example spec
   qtype validate examples/hello_world.qtype.yaml
   ```

7. **Update documentation** if needed

8. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

### Adding New Dependencies

When adding new dependencies, update `pyproject.toml`:

```toml
[project]
dependencies = [
    "jsonschema>=4.24.0",
    "pydantic>=2.11.5",
    "pyyaml>=6.0.2",
    "your-new-dependency>=1.0.0",
]
```

Then update the lock file:

```bash
uv lock
```

## Next Steps

After setting up your development environment:

1. Explore the `examples/` directory to understand QType specifications
2. Run the existing tests to ensure everything works
3. Read the documentation in `docs/`
4. Look at open issues for contribution opportunities
5. Start with small improvements or bug fixes

Happy coding! 🚀
