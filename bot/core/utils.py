import time
from typing import Callable, Any

def get_timestamp_ms() -> int:
    """Return current timestamp in milliseconds."""
    return int(time.time() * 1000)

async def retry_async(func: Callable, retries: int = 3, delay: float = 1.0, *args, **kwargs) -> Any:
    """Retry an async function multiple times."""
    import asyncio
    import logging
    
    logger = logging.getLogger("RetryHelper")
    last_exception = None
    
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                
    raise last_exception
