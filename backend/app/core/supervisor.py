"""Supervision for long-running background tasks (Kafka consumers).

Previously the consumers were fire-and-forget ``asyncio.create_task`` calls: an
exception (e.g. Kafka down at startup) killed them silently while the app kept
reporting healthy. The supervisor restarts them with exponential backoff.
"""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


async def supervise(
    coro_factory: Callable[[], Awaitable[None]],
    name: str,
    initial_backoff: float = 1.0,
    max_backoff: float = 60.0,
) -> None:
    backoff = initial_backoff
    while True:
        try:
            logger.info("Starting supervised task %r", name)
            await coro_factory()
            logger.warning("Supervised task %r exited cleanly; restarting", name)
            backoff = initial_backoff
        except asyncio.CancelledError:
            logger.info("Supervised task %r cancelled", name)
            raise
        except Exception:
            logger.exception("Supervised task %r crashed; restarting in %.1fs", name, backoff)
        await asyncio.sleep(backoff + random.uniform(0, backoff / 2))
        backoff = min(backoff * 2, max_backoff)
