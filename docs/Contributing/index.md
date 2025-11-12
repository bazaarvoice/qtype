# Contributing

Welcome to the QType development guide! This document provides comprehensive instructions for setting up your development environment and contributing to the project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Environment Setup](#development-environment-setup)
- [Using QType Commands](#using-qtype-commands)
- [Running Tests](#running-tests)
- [Code Quality and Standards](#code-quality-and-standards)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Next Steps](#next-steps)

## Prerequisites

- **Python 3.10 or higher** (this project targets Python 3.10+)
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

# Install all dependencies, development tools, and qtype in editable mode
uv sync --extra interpreter
```

This single command installs everything you need, including the `qtype` package in editable mode so changes to the source code are immediately reflected.

## Using QType Commands

After installation, activate the virtual environment:
```bash
source ./venv/bin/activate
```

You may see `(qtype)` on yout terminal if you are in bash

After installation, you should be able to run the `qtype` command from anywhere:

```bash
qtype --help
```

## Running Tests

The project uses pytest for testing with coverage measurement:

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=qtype

# Run tests with coverage and generate HTML report
uv run pytest --cov=qtype --cov-report=html

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_loader_file_inclusion.py

# Run specific test class
uv run pytest tests/test_loader_file_inclusion.py::TestFileIncludeLoader

# Run specific test method
uv run pytest tests/test_loader_file_inclusion.py::TestFileIncludeLoader::test_include_yaml_file

# Run tests matching a pattern
uv run pytest -k "test_include"

# Run tests with specific markers
uv run pytest -m "not network"  # Skip network tests
uv run pytest -m "not slow"     # Skip slow tests

# Run tests in parallel (if pytest-xdist is installed)
uv run pytest -n auto
```

### Coverage Reports

Coverage reports show:
- Which lines of code are executed during tests
- Which lines are missing test coverage  
- Overall coverage percentage for each module
- HTML report with line-by-line coverage highlighting

The HTML coverage report (`htmlcov/index.html`) provides the most detailed view, showing exactly which lines need more test coverage.

### Test Markers

The project uses pytest markers to categorize tests:
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.network`: Tests requiring network access

Skip specific test categories:
```bash
# Skip slow tests
uv run pytest -m "not slow"

# Skip network tests
uv run pytest -m "not network"

# Run only network tests
uv run pytest -m "network"
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

#### Format code automatically:

```bash
# Format with ruff
ruff format qtype/ tests/

# Lint with ruff
ruff check qtype/ tests/

# Sort imports
isort qtype/ tests/

# Type checking with mypy
mypy qtype/ tests/
```

#### Pre-commit hooks (Optional but recommended):

```bash
uv pip install pre-commit
pre-commit install
```

Settings are in `.pre-commit-config.yaml`:


##  Project Structure

- `qtype/` – Python package for parsing, validating, and interpreting QType specs
- `examples/` – Example `.qtype.yaml` specs
- `schema/` – JSON Schema auto-generated from the DSL
- `docs/` – Documentation 
- `tests/` – Unit and integration tests

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
   uv run pytest --cov=qtype
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
   ptython -m qtype.cli generate-schema -o schema/test.json
   
   # Validate example spec
   ptython -m qtype.cli validate examples/hello_world.qtype.yaml
   ```

7. **Update documentation** if needed

8. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

### How To: Expand The DSL

The core of qtype is the DSL specified in [qtype/dsl/model.py](https://github.com/bazaarvoice/qtype/blob/main/qtype/dsl/model.py). All functionality is rooted in the pydantic classes in that file. To expand the dsl with new classes, types, etc., edit this file. If your new class is a subtype (like a Step, etc) you should make sure you update any unions (like `StepType` etc)

Once you have it to your liking, you can generate the new schema:
```
qtype generate schema -o schema/qtype.schema.json 
```

You can make vscode validate it with your newly generated schema by adding it to your `settings.json`:
```
"yaml.schemas" : {
   "schema/qtype.schema.json": ["qtype.config.yaml", "*.qtype.yaml"],
},
```

The semantic version of [qtype/semantic/model.py](https://github.com/bazaarvoice/qtype/blob/main/qtype/semantic/model.py) can also be automatically generated:
```
qtype generate semantic-model
```

Next, update [qtype/semantic/checker.py](https://github.com/bazaarvoice/qtype/blob/main/qtype/semantic/checker.py) to enforce any semantic rules for your step.

Next, make a canonical example of your new type in the `examples` folder (e.g., `examples/new_type_example.qtype.yaml`) and it can be validated:
```
qtype validate examples/new_type_example.qtype.yaml
```

The docstrings in the types are used to update the documentation with:
```
qtype generate dsl-docs
```

Finally, if desired, you can update the interpreter to support your new type. If your new type is a `Step`, you can add an `executor` in the [qtype/interpreter/executors](https://github.com/bazaarvoice/qtype/tree/main/qtype/interpreter/executors) folder and then update the [qtype/interpreter/base/factory.py](https://github.com/bazaarvoice/qtype/blob/main/qtype/interpreter/base/factory.py).


### Adding New Dependencies

When adding new dependencies, use uv to add to `pyproject.toml`:

```bash
uv add <dependency>
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
