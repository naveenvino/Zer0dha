import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def retry(exceptions, tries=3, delay=1, backoff=2, logger=logger):
    """
    Retry calling the decorated function using an exponential backoff.

    Args:
        exceptions: The exception(s) to catch and retry on.
        tries: Number of times to try (not including the first attempt).
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for the delay between retries.
        logger: Logger to use for logging retry attempts.
    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"{str(e)}, Retrying in {mdelay} seconds...")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs) # Last attempt
        return f_retry
    return deco_retry
