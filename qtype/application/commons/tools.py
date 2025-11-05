import base64
from datetime import datetime, timezone

from pydantic import BaseModel

#
# -------------  Encoding/Decoding -------------
#


def base64_encode(data: bytes) -> str:
    """
    Encode bytes to a Base64 string.

    Args:
        data: Bytes to encode.

    Returns:
        Base64 encoded string.
    """
    return base64.b64encode(data).decode("utf-8")


def base64_decode(data: str) -> bytes:
    """
    Decode a Base64 string to bytes.

    Args:
        data: Base64 encoded string.

    Returns:
        Decoded bytes.
    """
    return base64.b64decode(data)


#
# -------------  Date/Time Operations -------------
#


def get_current_timestamp() -> datetime:
    """
    Get the current UTC timestamp.

    Returns:
        Current timestamp as datetime object.
    """
    return datetime.now(timezone.utc)


def timedelta(
    timestamp: datetime,
    days: int = 0,
    seconds: int = 0,
    microseconds: int = 0,
    milliseconds: int = 0,
    minutes: int = 0,
    hours: int = 0,
    weeks: int = 0,
) -> datetime:
    """
    Add a specified amount of time from a given timestamp.

    This function takes a datetime object and adjusts it by adding a combination of
    time units such as days, seconds, microseconds, milliseconds, minutes, hours,
    and weeks.

    Args:
        timestamp (datetime): The original datetime object to adjust.
        days (int, optional): Number of days to add or subtract. Defaults to 0.
        seconds (int, optional): Number of seconds to add or subtract. Defaults to 0.
        microseconds (int, optional): Number of microseconds to add or subtract. Defaults to 0.
        milliseconds (int, optional): Number of milliseconds to add or subtract. Defaults to 0.
        minutes (int, optional): Number of minutes to add or subtract. Defaults to 0.
        hours (int, optional): Number of hours to add or subtract. Defaults to 0.
        weeks (int, optional): Number of weeks to add or subtract. Defaults to 0.

    Returns:
        datetime: A new datetime object with the adjusted time.

    Example:
        >>> from datetime import datetime
        >>> original_time = datetime(2023, 10, 1, 12, 0, 0)
        >>> new_time = timedelta(original_time, days=1, hours=2)
        >>> print(new_time)
        2023-10-02 14:00:00
    """
    from datetime import timedelta as timedelta_impl

    return timestamp + timedelta_impl(
        days=days,
        seconds=seconds,
        microseconds=microseconds,
        milliseconds=milliseconds,
        minutes=minutes,
        hours=hours,
        weeks=weeks,
    )


class TimeDifferenceResultType(BaseModel):
    total_seconds: float
    total_minutes: float
    total_hours: float
    total_days: float
    days: int
    seconds: int
    microseconds: int


def calculate_time_difference(
    start_time: datetime, end_time: datetime
) -> TimeDifferenceResultType:
    """
    Calculate the difference between two timestamps.

    Args:
        start_time: Starting datetime object.
        end_time: Ending datetime object.

    Returns:
        Dictionary with difference in various units (seconds, minutes, hours, days).
    """
    diff = end_time - start_time
    total_seconds = diff.total_seconds()

    return TimeDifferenceResultType(
        total_seconds=total_seconds,
        total_minutes=total_seconds / 60,
        total_hours=total_seconds / 3600,
        total_days=total_seconds / 86400,
        days=diff.days,
        seconds=diff.seconds,
        microseconds=diff.microseconds,
    )


def parse_duration_string(duration: str) -> int:
    """
    Parse a human-readable duration string into seconds.

    Args:
        duration: Duration string like "1h 30m", "2 days", "45 minutes".

    Returns:
        Total duration in seconds.

    Raises:
        ValueError: If duration format is not recognized.
    """
    import re

    # Convert to lowercase and normalize
    duration = duration.lower().strip()

    # Define patterns for different time units
    patterns = {
        r"(\d+)\s*(?:sec|second|seconds|s)": 1,
        r"(\d+)\s*(?:min|minute|minutes|m)": 60,
        r"(\d+)\s*(?:hour|hours|h)": 3600,
        r"(\d+)\s*(?:day|days|d)": 86400,
        r"(\d+)\s*(?:week|weeks|w)": 604800,
    }

    total_seconds = 0
    found_match = False

    for pattern, multiplier in patterns.items():
        matches = re.findall(pattern, duration)
        for match in matches:
            total_seconds += int(match) * multiplier
            found_match = True

    if not found_match:
        raise ValueError(f"Unable to parse duration: {duration}")

    return total_seconds


def format_datetime(timestamp: datetime, format_string: str) -> str:
    """
    Format a timestamp using a custom format string that can be passed to strftime.

    Args:
        timestamp: Datetime object to format.
        format_string: Python datetime format string (e.g., "%Y-%m-%d %H:%M:%S").

    Returns:
        Formatted datetime string.
    """
    return timestamp.strftime(format_string)
