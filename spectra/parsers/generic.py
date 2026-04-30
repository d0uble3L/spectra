from __future__ import annotations


def parse(raw: str) -> str:
    """Pass-through for raw text scanner output (Nessus .nessus export,
    manual pentest notes, or any unrecognized format).
    Adds a minimal header so Claude knows it's unstructured input."""
    header = "=== SECURITY SCAN OUTPUT (generic / unstructured format) ===\n\n"
    return header + raw.strip()
