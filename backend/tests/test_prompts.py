"""Prompt registry and prompt content contracts."""

import re

import pytest

from app.prompts import get_prompt, registry

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
INTERVIEWER_PROMPTS = ["interviewer.question", "interviewer.evaluate", "interviewer.summarize"]
CHARACTER_PROMPTS = ["character.positive.ua", "character.negative.ua"]

# Markers of the old "roast" persona that must never come back.
BANNED_CRUELTY_MARKERS = ["Scratch", "WordPress", "Excel", "No-code", "котик", "дівчина"]


def test_registry_loads_all_expected_prompts():
    names = {p.name for p in registry.all()}
    assert set(INTERVIEWER_PROMPTS) <= names
    assert set(CHARACTER_PROMPTS) <= names


def test_all_prompts_have_semver_and_params():
    for prompt in registry.all():
        assert SEMVER.match(prompt.version), f"{prompt.name} has bad version {prompt.version}"
        assert prompt.template, f"{prompt.name} has empty template"
        assert "temperature" in prompt.params, f"{prompt.name} missing temperature"
        assert "max_tokens" in prompt.params, f"{prompt.name} missing max_tokens"


def test_unknown_prompt_raises_key_error():
    with pytest.raises(KeyError):
        get_prompt("does.not.exist")


@pytest.mark.parametrize("name", INTERVIEWER_PROMPTS)
def test_interviewer_templates_render(name):
    text = get_prompt(name).render(level="junior", topic="Python")
    assert "junior" in text
    assert "Python" in text


@pytest.mark.parametrize("name", CHARACTER_PROMPTS)
def test_character_prompts_mention_industry_legends(name):
    template = get_prompt(name).template
    assert "Torvalds" in template
    assert "Karpathy" in template


@pytest.mark.parametrize("name", CHARACTER_PROMPTS)
def test_character_prompts_have_injection_hardening(name):
    assert "XML" in get_prompt(name).template


def test_negative_prompt_has_no_roast_content():
    template = get_prompt("character.negative.ua").template
    for marker in BANNED_CRUELTY_MARKERS:
        assert marker not in template, f"cruelty marker {marker!r} found in negative prompt"


def test_negative_prompt_is_constructive():
    template = get_prompt("character.negative.ua").template
    assert "Заборонено" in template
    assert "конструктив" in template
