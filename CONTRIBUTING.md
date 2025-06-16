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

#### Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync
```

#### Using pip and venv (Alternative)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt  # If you create one from pyproject.toml
```

## Installing QType for Development

Install QType in editable mode so changes to the source code are immediately reflected:

### Using uv

```bash
# Install in development mode
uv pip install -e .

# Or if you want to install with specific development dependencies
uv pip install -e ".[dev]"  # If dev extras are defined in pyproject.toml
```

### Using pip

```bash
# Activate your virtual environment first
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install in editable mode
pip install -e .
```

After installation, you should be able to run the `qtype` command from anywhere:

```bash
qtype --help
```

## Running Tests

Currently, the project has a basic test structure. Here's how to run tests:

### Using Python's unittest module

```bash
# Run all tests
python -m unittest discover tests/

# Run specific test file
python -m unittest tests.test_loader
python -m unittest tests.test_ir_resolution
```

### Using pytest (Recommended for development)

If you prefer pytest, install it first:

```bash
# With uv
uv pip install pytest

# With pip
pip install pytest
```

Then run tests:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_loader.py

# Run with coverage (install pytest-cov first)
uv pip install pytest-cov
pytest --cov=qtype tests/
```

### Setting up Test Configuration

Create a `pytest.ini` file in the project root for consistent test configuration:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
```

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

### Recommended Development Tools

Install these tools for better development experience:

```bash
# Code formatting and linting
uv pip install black isort flake8 mypy

# Or with pip
pip install black isort flake8 mypy
```

#### Format code automatically:

```bash
# Format with black
black qtype/ tests/

# Sort imports
isort qtype/ tests/

# Check style with flake8
flake8 qtype/ tests/

# Type checking with mypy
mypy qtype/
```

#### Pre-commit hooks (Optional but recommended):

```bash
uv pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.0.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
```

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
   python -m unittest discover tests/
   # or
   pytest
   ```

5. **Check code quality:**
   ```bash
   black qtype/ tests/
   isort qtype/ tests/
   flake8 qtype/ tests/
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

## CLI Usage

The QType CLI provides two main commands:

### Generate JSON Schema

```bash
# Output to stdout
qtype generate-schema

# Save to file
qtype generate-schema -o schema/qtype.schema.json
```

### Validate QType Specifications

```bash
# Validate a QType YAML file
qtype validate examples/hello_world.qtype.yaml

# Enable debug logging
qtype --log-level DEBUG validate examples/hello_world.qtype.yaml
```

## Troubleshooting

### Common Issues

1. **Import errors after installation:**
   - Ensure you're using the correct Python environment
   - Reinstall in editable mode: `pip install -e .`

2. **Test failures:**
   - Check that all dependencies are installed
   - Ensure you're running tests from the project root

3. **Type checking errors:**
   - Make sure all function signatures have type hints
   - Check that imports are properly typed

4. **CLI command not found:**
   - Verify installation: `pip show qtype`
   - Check that the virtual environment is activated

### Getting Help

- Check existing [issues](https://github.com/yourusername/qtype/issues)
- Create a new issue with detailed information about your problem
- Include Python version, operating system, and error messages

## Development Dependencies

Core dependencies (from `pyproject.toml`):
- `jsonschema>=4.24.0` - JSON schema validation
- `pydantic>=2.11.5` - Data validation and serialization  
- `pyyaml>=6.0.2` - YAML parsing

Additional development dependencies you may want to install:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Type checking
- `pre-commit` - Git hooks

## Next Steps

After setting up your development environment:

1. Explore the `examples/` directory to understand QType specifications
2. Run the existing tests to ensure everything works
3. Read the documentation in `docs/`
4. Look at open issues for contribution opportunities
5. Start with small improvements or bug fixes

Happy coding! 🚀
