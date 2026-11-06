from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Returns current UTC time as a timezone-naive datetime.

    MySQL DATETIME does not preserve timezone information.
    We consistently store UTC values.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)