"""promptfoo prompt functions — thin adapters over the backend prompt registry.

Keeps the eval suite on the exact same prompt source of truth as production.
promptfoo calls each function with a context dict ({"vars": {...}}) and expects
a string back; a JSON message array lets us set the system prompt.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.prompts import get_prompt  # noqa: E402


def _character_user_message(v: dict) -> str:
    return (
        f"<question>{v['question']}</question>\n"
        f"<candidate_answer>{v['answer']}</candidate_answer>\n"
        f"<score>{v['score']}/10</score>\n"
        f"<evaluator_feedback>{v['feedback']}</evaluator_feedback>"
    )


def _character(sentiment: str, context: dict) -> str:
    v = context["vars"]
    prompt = get_prompt(f"character.{sentiment}.{v.get('lang', 'ua')}")
    return json.dumps(
        [
            {"role": "system", "content": prompt.template},
            {"role": "user", "content": _character_user_message(v)},
        ]
    )


def character_positive(context: dict) -> str:
    return _character("positive", context)


def character_negative(context: dict) -> str:
    return _character("negative", context)


def interviewer_question(context: dict) -> str:
    v = context["vars"]
    system = get_prompt("interviewer.question").render(level=v["level"], topic=v["topic"])
    return json.dumps(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": "Generate the first question."},
        ]
    )
