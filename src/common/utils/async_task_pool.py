import asyncio
from typing import Iterable, Awaitable, Any


async def async_run_tasks(coroutines: Iterable[Awaitable], concurrency) -> list[Any]:
    """
    :param coroutines: An iterable object for the coroutine to execute (e.g., list, tuple, etc.).
    :param concurrency: Maximum concurrent number.
    :return: Tuple of all coroutine execution results.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def wrapped_task(coro: Awaitable) -> Awaitable:
        async with semaphore:
            return await coro

    tasks = [asyncio.create_task(wrapped_task(coro)) for coro in coroutines]

    results = await asyncio.gather(*tasks)
    return results