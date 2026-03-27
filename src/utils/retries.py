import time
from typing import Callable

def retry_with_backoff(retries: int = 3, backoff_in_seconds: float = 1.0):
    """
    Exponential Backoff retry decorator.
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        print(f"[ERROR] Max retries reached for {func.__name__}: {e}")
                        return None
                    sleep = (backoff_in_seconds * 2 ** x)
                    print(f"[WARNING] Retry {x+1}/{retries} for {func.__name__} after {sleep:.1f}s due to error: {e}")
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator
