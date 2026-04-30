from __future__ import annotations


def parse(data: dict) -> str:
    """Normalize Trivy JSON output into a clean text representation for Claude."""
    lines: list[str] = []
    lines.append("=== TRIVY VULNERABILITY SCAN ===")
    lines.append(f"Target     : {data.get('ArtifactName', 'Unknown')}")
    lines.append(f"Type       : {data.get('ArtifactType', 'Unknown')}")

    metadata = data.get("Metadata", {})
    os_info = metadata.get("OS", {})
    if os_info:
        lines.append(f"OS         : {os_info.get('Family', '')} {os_info.get('Name', '')}")

    total_vulns = 0
    for result in data.get("Results", []):
        vulns = result.get("Vulnerabilities") or []
        misconfigs = result.get("Misconfigurations") or []
        secrets = result.get("Secrets") or []
        total_vulns += len(vulns) + len(misconfigs) + len(secrets)

    lines.append(f"Total Raw  : {total_vulns} findings")
    lines.append("")

    for result in data.get("Results", []):
        target = result.get("Target", "unknown")
        result_type = result.get("Type", "unknown")

        vulns = result.get("Vulnerabilities") or []
        if vulns:
            lines.append(f"--- {target} [{result_type}] — {len(vulns)} vulnerabilities ---")
            for v in vulns:
                sev = v.get("Severity", "UNKNOWN")
                vid = v.get("VulnerabilityID", "N/A")
                pkg = v.get("PkgName", "unknown")
                installed = v.get("InstalledVersion", "?")
                fixed = v.get("FixedVersion", "")
                title = v.get("Title", v.get("Description", "")[:120])

                lines.append(f"[{sev}] {vid}")
                lines.append(f"  Package  : {pkg} {installed}")
                if fixed:
                    lines.append(f"  Fixed in : {fixed}")
                if title:
                    lines.append(f"  Summary  : {title}")

                cvss = v.get("CVSS", {})
                for source, scores in cvss.items():
                    v3 = scores.get("V3Score")
                    if v3 is not None:
                        lines.append(f"  CVSS v3  : {v3} ({source})")
                        break

                refs = v.get("References", [])
                if refs:
                    lines.append(f"  Refs     : {refs[0]}")
                lines.append("")

        misconfigs = result.get("Misconfigurations") or []
        if misconfigs:
            lines.append(f"--- {target} — {len(misconfigs)} misconfigurations ---")
            for m in misconfigs:
                sev = m.get("Severity", "UNKNOWN")
                mid = m.get("ID", "N/A")
                title = m.get("Title", "")
                desc = m.get("Description", "")[:200]
                resolution = m.get("Resolution", "")
                lines.append(f"[{sev}] {mid}: {title}")
                if desc:
                    lines.append(f"  Detail   : {desc}")
                if resolution:
                    lines.append(f"  Fix      : {resolution}")
                lines.append("")

        secrets = result.get("Secrets") or []
        if secrets:
            lines.append(f"--- {target} — {len(secrets)} secrets detected ---")
            for s in secrets:
                sev = s.get("Severity", "HIGH")
                category = s.get("Category", "secret")
                title = s.get("Title", "")
                match = s.get("Match", "")[:60]
                lines.append(f"[{sev}] {category}: {title}")
                if match:
                    lines.append(f"  Match    : {match}...")
                lines.append("")

    return "\n".join(lines)
