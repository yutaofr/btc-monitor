from datetime import datetime, timezone
from typing import Optional

def check_freshness(obs_timestamp: datetime, ttl_hours: int, current_time: Optional[datetime] = None) -> bool:
    """
    Returns True if the observation timestamp is within the TTL window relative to current_time.
    If current_time is None, uses datetime.now().
    """
    if current_time is None:
        current_time = datetime.now()
        
    # Standardize to naive datetimes to avoid TypeError when mixing aware/naive
    # Factor timestamps are often naive from indicator fetchers
    t1 = current_time.replace(tzinfo=None)
    t2 = obs_timestamp.replace(tzinfo=None)
    
    delta = t1 - t2
    max_delta_seconds = ttl_hours * 3600
    
    return delta.total_seconds() <= max_delta_seconds
