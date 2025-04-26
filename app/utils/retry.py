from functools import wraps
from typing import Callable, TypeVar, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

T = TypeVar('T')

def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
    retry_on: tuple = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    重試裝飾器
    
    Args:
        max_attempts: 最大重試次數
        min_wait: 最小等待時間（秒）
        max_wait: 最大等待時間（秒）
        retry_on: 需要重試的異常類型元組
    
    Returns:
        裝飾器函數
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(retry_on)
        )
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def with_sync_retry(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
    retry_on: tuple = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    同步重試裝飾器
    
    Args:
        max_attempts: 最大重試次數
        min_wait: 最小等待時間（秒）
        max_wait: 最大等待時間（秒）
        retry_on: 需要重試的異常類型元組
    
    Returns:
        裝飾器函數
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(retry_on)
        )
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return func(*args, **kwargs)
        
        return wrapper
    return decorator 