"""Sample utility module for testing tool generation."""

from datetime import datetime


def calculate_age(birth_date: datetime, reference_date: datetime) -> int:
    """Calculate age in years between two dates.

    Args:
        birth_date: The birth date
        reference_date: The date to calculate age at

    Returns:
        Age in complete years
    """
    age = reference_date.year - birth_date.year
    if (reference_date.month, reference_date.day) < (
        birth_date.month,
        birth_date.day,
    ):
        age -= 1
    return age


def greeting(name: str, title: str = "Mr.") -> str:
    """Generate a greeting message.

    Args:
        name: The person's name
        title: The person's title (optional)

    Returns:
        A formatted greeting message
    """
    return f"Hello, {title} {name}!"
