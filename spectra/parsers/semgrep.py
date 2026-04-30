from __future__ import annotations


_SEVERITY_MAP = {
    "ERROR": "HIGH",
    "WARNING": "MEDIUM",
    "INFO": "LOW",
}


def parse(data: dict) -> str:
    """Normalize Semgrep JSON output into a clean text representation for Claude."""
    results = data.get("results", [])
    errors = data.get("errors", [])
    stats = data.get("stats", {})

    lines: list[str] = []
    lines.append("=== SEMGREP SAST SCAN ===")
    lines.append(f"Findings   : {len(results)}")
    lines.append(f"Scan Errors: {len(errors)}")
    if stats:
        lines.append(f"Stats      : {stats}")
    lines.append("")

    grouped: dict[str, list[dict]] = {}
    for r in results:
        path = r.get("path", "unknown")
        grouped.setdefault(path, []).append(r)

    for path, findings in sorted(grouped.items()):
        lines.append(f"--- {path} ({len(findings)} findings) ---")
        for f in findings:
            extra = f.get("extra", {})
            raw_sev = extra.get("severity", "WARNING")
            sev = _SEVERITY_MAP.get(raw_sev.upper(), raw_sev)
            check_id = f.get("check_id", "unknown-rule")
            start_line = f.get("start", {}).get("line", "?")
            end_line = f.get("end", {}).get("line", "?")
            message = extra.get("message", "").strip()

            metadata = extra.get("metadata", {})
            cwe = metadata.get("cwe", [])
            owasp = metadata.get("owasp", [])
            confidence = metadata.get("confidence", "")
            references = metadata.get("references", [])

            lines.append(f"[{sev}] {check_id}")
            lines.append(f"  Location : line {start_line}–{end_line}")
            if message:
                lines.append(f"  Message  : {message[:300]}")
            if confidence:
                lines.append(f"  Confidence: {confidence}")
            if cwe:
                lines.append(f"  CWE      : {', '.join(cwe[:3])}")
            if owasp:
                lines.append(f"  OWASP    : {', '.join(owasp[:3])}")
            if references:
                lines.append(f"  Refs     : {references[0]}")

            code_snippet = extra.get("lines", "").strip()
            if code_snippet:
                lines.append(f"  Code     : {code_snippet[:200]}")
            lines.append("")

    if errors:
        lines.append("--- Scan Errors ---")
        for e in errors:
            lines.append(f"  {e}")
        lines.append("")

    return "\n".join(lines)
