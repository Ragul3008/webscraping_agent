import asyncio
from typing import List, Callable, Any


async def run_with_concurrency(
    limit: int,
    tasks: List[Callable],
):
    """
    Run async tasks with concurrency limit.
    """

    semaphore = asyncio.Semaphore(limit)

    async def sem_task(task):

        async with semaphore:

            return await task

    return await asyncio.gather(
        *(sem_task(task) for task in tasks),
        return_exceptions=True
    )


async def retry_async(
    func,
    retries: int = 3,
    delay: float = 1.0
):
    """
    Retry async function.
    """

    for attempt in range(retries):

        try:

            return await func()

        except Exception:

            if attempt == retries - 1:
                raise

            await asyncio.sleep(delay)