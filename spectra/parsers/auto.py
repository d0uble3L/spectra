from __future__ import annotations

import json
from typing import Optional

from . import generic, semgrep, trivy


def detect_and_normalize(raw: str, hint: str = "auto") -> str:
    """
    Detect scanner format and return a normalized string ready for Claude.

    hint: "auto" | "trivy" | "semgrep" | "generic"
    """
    if hint == "trivy":
        return _try_trivy(raw) or generic.parse(raw)
    if hint == "semgrep":
        return _try_semgrep(raw) or generic.parse(raw)
    if hint == "generic":
        return generic.parse(raw)

    # auto-detect
    data = _try_parse_json(raw)
    if data is not None:
        if _is_trivy(data):
            return trivy.parse(data)
        if _is_semgrep(data):
            return semgrep.parse(data)

    return generic.parse(raw)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _try_parse_json(raw: str) -> "dict | list | None":
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None


def _try_trivy(raw: str) -> "Optional[str]":
    data = _try_parse_json(raw)
    if data and _is_trivy(data):
        return trivy.parse(data)
    return None


def _try_semgrep(raw: str) -> "Optional[str]":
    data = _try_parse_json(raw)
    if data and _is_semgrep(data):
        return semgrep.parse(data)
    return None


def _is_trivy(data: "dict | list") -> bool:
    if not isinstance(data, dict):
        return False
    return "Results" in data and "ArtifactName" in data


def _is_semgrep(data: "dict | list") -> bool:
    if not isinstance(data, dict):
        return False
    return "results" in data and isinstance(data.get("results"), list)
