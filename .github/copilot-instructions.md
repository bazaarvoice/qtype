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

 All Python code generated for this repository *should*:
    - Use logging instead of print statements for debug/info/error messages
    - Use `__init__.py` files to mark directories as Python packages
    - Use `__main__.py` for executable scripts
    - Use `pydantic BaseModel` for simple data structures

This project is using python 3.9, so you should not use any features that are not available in Python 3.9.
You should, however, use features that are available in Python 3.9. Some examples are:
    - Type hinting with `typing` module
    - f-strings for string formatting
    - Dictionary merging with `|` operator
    - New syntax for union types (e.g., `int | str`)
 