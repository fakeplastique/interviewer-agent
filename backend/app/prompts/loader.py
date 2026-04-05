"""Versioned prompt registry.

Prompts live as YAML files under ``definitions/``. Each entry carries a semver
``version`` and the generation ``params`` (temperature, max_tokens) it was tuned
with, so prompt text and sampling parameters version together. Bump the version
and record the change in ``CHANGELOG.md`` whenever a template changes.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_DEFINITIONS_DIR = Path(__file__).parent / "definitions"
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    description: str
    template: str
    params: dict[str, Any] = field(default_factory=dict)

    def render(self, **kwargs: Any) -> str:
        return self.template.format(**kwargs)


class PromptRegistry:
    def __init__(self, definitions_dir: Path = _DEFINITIONS_DIR):
        self._prompts: dict[str, Prompt] = {}
        for path in sorted(definitions_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            for entry in data["prompts"]:
                prompt = Prompt(
                    name=entry["name"],
                    version=entry["version"],
                    description=entry.get("description", ""),
                    template=entry["template"].strip(),
                    params=entry.get("params", {}),
                )
                if not _SEMVER_RE.match(prompt.version):
                    raise ValueError(
                        f"Prompt {prompt.name!r} in {path.name} has non-semver "
                        f"version {prompt.version!r}"
                    )
                if prompt.name in self._prompts:
                    raise ValueError(f"Duplicate prompt name {prompt.name!r} in {path.name}")
                self._prompts[prompt.name] = prompt

    def get(self, name: str) -> Prompt:
        if name not in self._prompts:
            raise KeyError(f"Unknown prompt {name!r}. Available: {sorted(self._prompts)}")
        return self._prompts[name]

    def all(self) -> list[Prompt]:
        return list(self._prompts.values())


registry = PromptRegistry()


def get_prompt(name: str) -> Prompt:
    return registry.get(name)
