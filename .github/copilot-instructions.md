# GitHub Copilot Instructions
 All Python code generated for this repository *must*:
    - Follow PEP8 style guidelines (https://peps.python.org/pep-0008/)
    - Use best practices for Python, including clear naming, docstrings, and type hints
    - Avoid unused imports and variables
    - Prefer explicit over implicit code
    - Use idiomatic Python constructs
    - Write functions and classes with clear responsibilities
    - Add comments where logic is non-obvious
    - Use consistent indentation (4 spaces)
    - Avoid long lines (>79 chars) unless necessary
    - Use f-strings for string interpolation
    - Prefer list/dict/set comprehensions where appropriate
    - Use snake_case for functions and variables, PascalCase for classes
    - Add docstrings to all public functions, classes, and modules
    - Avoid bare excepts; catch specific exceptions
    - Use type hints for all function signatures and class attributes
    - Write readable, maintainable, and testable code
    
 All Python code generated for this repository *must* pass the following tools:
    
    ## mypy compliance:
    - Use proper type annotations for all function parameters, return values, and class attributes
    - Import types from `typing` module when needed (List, Dict, Optional, Union, etc.)
    - Use `from __future__ import annotations` for forward references when needed
    - Avoid `Any` type unless absolutely necessary
    - Use generic types appropriately (e.g., `List[str]`, `Dict[str, int]`)
    - Handle Optional types explicitly with proper None checks
    - Use type: ignore comments sparingly and only with specific error codes
    
    ## isort compliance:
    - Group imports in the following order: standard library, third-party, local imports
    - Separate import groups with blank lines
    - Sort imports alphabetically within each group
    - Use `from` imports for specific items when appropriate
    - Place `from __future__ import annotations` at the very top
    
    ## ruff compliance:
    - Follow all ruff default rules and error codes
    - Avoid unused variables (prefix with underscore if intentionally unused)
    - Remove unused imports
    - Use consistent quote styles (prefer double quotes)
    - Avoid mutable default arguments (use None and initialize in function body)
    - Use pathlib for file operations instead of os.path
    - Prefer comprehensions over map/filter where readable
    - Use context managers for resource management
    - Avoid lambda assignments (use def for named functions)
    - Use enumerate() instead of manual counters
    - Use zip() for parallel iteration

 All Python code generated for this repository *should*:
    - Use logging instead of print statements for debug/info/error messages
    - Use `__init__.py` files to mark directories as Python packages
    - Use `__main__.py` for executable scripts
    - Use `pydantic BaseModel` for simple data structures

This project is using python 3.9, so you should not use any features that are not available in Python 3.9.
You should, however, use features that are available in Python 3.9. Some examples are:
    - Type hinting with `typing` module (use `typing.List` instead of `list`, `typing.Dict` instead of `dict`, etc.)
    - f-strings for string formatting
    - Dictionary merging with `|` operator
    - Use `typing.Union` instead of `|` for union types (e.g., `Union[int, str]` not `int | str`)
    - Use `typing.Optional` for optional parameters
    - Use `from __future__ import annotations` for forward references and string annotations
 