from datetime import datetime, time, date
from zoneinfo import ZoneInfo

def combine_datetime_with_timezone(d: date, t: time, tz_str: str) -> datetime:
    """
    Helper to combine date + time + timezone -> UTC Datetime.
    Used by both Schemas (Create) and Service (Update).
    """
    tz = ZoneInfo(tz_str)
    local_dt = datetime.combine(d, t)

    # 1. Attach the specific timezone (e.g., "Africa/Lagos")
    # 2. Convert to UTC for storage
    return local_dt.replace(tzinfo=tz).astimezone(ZoneInfo("UTC"))