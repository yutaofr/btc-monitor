from datetime import datetime, timezone
from typing import Optional

def check_freshness(obs_timestamp: datetime, ttl_hours: int, current_time: Optional[datetime] = None) -> bool:
    """
    Returns True if the observation timestamp is within the TTL window relative to current_time.
    If current_time is None, uses datetime.now().
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    elif current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
        
    # Standardize observation to UTC as well
    if obs_timestamp.tzinfo is None:
        obs_timestamp = obs_timestamp.replace(tzinfo=timezone.utc)
    else:
        obs_timestamp = obs_timestamp.astimezone(timezone.utc)

    delta = (current_time - obs_timestamp).total_seconds()
    max_delta_seconds = ttl_hours * 3600
    
    # Reject future dates (delta < 0) and stale dates (delta > max)
    return 0 <= delta <= max_delta_seconds
