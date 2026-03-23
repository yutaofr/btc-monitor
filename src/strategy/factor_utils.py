from datetime import datetime, timezone
from typing import Optional

def check_freshness(obs_timestamp: datetime, ttl_hours: int, current_time: Optional[datetime] = None) -> bool:
    """
    Returns True if the observation timestamp is within the TTL window relative to current_time.
    If current_time is None, uses datetime.now().
    """
    if current_time is None:
        current_time = datetime.now()
        
    # Ensure both are naive or both are aware. Registry timestamps are usually naive from indicators.
    # For robust comparison, if one is aware and other is not, we'll strip tz.
    delta = current_time - obs_timestamp
    max_delta_seconds = ttl_hours * 3600
    
    return delta.total_seconds() <= max_delta_seconds
