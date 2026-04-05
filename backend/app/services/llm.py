"""Anthropic chat clients with per-task generation params and structured-output fallback.

Generation params live next to the prompt text in ``app/prompts/definitions``
so both version together.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage

from app.config import settings
from app.prompts import get_prompt

logger = logging.getLogger(__name__)

T = TypeVar("T")


def make_chat(temperature: float, max_tokens: int) -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.ANTHROPIC_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=settings.LLM_MAX_RETRIES,
    )


def chat_for_prompt(prompt_name: str) -> ChatAnthropic:
    params = get_prompt(prompt_name).params
    return make_chat(params["temperature"], params["max_tokens"])


question_llm = chat_for_prompt("interviewer.question")
eval_llm = chat_for_prompt("interviewer.evaluate")
summary_llm = chat_for_prompt("interviewer.summarize")


async def invoke_structured(
    chain,
    messages: list[BaseMessage],
    fallback_factory: Callable[[], T | Awaitable[T]] | None = None,
) -> T:
    """Invoke a structured-output chain with one corrective retry and a fallback.

    A hard failure here would otherwise be swallowed by the Kafka consumer's
    blanket exception handler, silently dropping the interview turn and leaving
    the client hanging — so degraded output beats no output.
    """
    try:
        return await chain.ainvoke(messages)
    except Exception:
        logger.warning("Structured LLM call failed, retrying with JSON nudge", exc_info=True)

    try:
        nudged = [
            *messages,
            HumanMessage(content="Return ONLY valid JSON matching the requested schema."),
        ]
        return await chain.ainvoke(nudged)
    except Exception:
        if fallback_factory is None:
            raise
        logger.exception("Structured LLM call failed twice; using fallback result")
        return fallback_factory()
