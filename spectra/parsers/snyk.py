from __future__ import annotations

from collections.abc import Iterable
from typing import Any

_SEVERITY_MAP = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
    "info": "INFO",
    "error": "HIGH",
    "warning": "MEDIUM",
    "note": "LOW",
}


def is_snyk(data: Any) -> bool:
    """Return whether parsed JSON has a recognizable Snyk result shape."""
    if isinstance(data, list):
        return bool(data) and all(is_snyk(item) for item in data)
    if not isinstance(data, dict):
        return False

    if "infrastructureAsCodeIssues" in data:
        return True
    if "vulnerabilities" in data and any(
        key in data
        for key in ("ok", "dependencyCount", "org", "projectName", "displayTargetFile", "docker")
    ):
        return True

    runs = data.get("runs")
    if not isinstance(runs, list):
        return False
    for run in runs:
        if not isinstance(run, dict):
            continue
        tool = run.get("tool")
        driver = tool.get("driver") if isinstance(tool, dict) else None
        name = driver.get("name", "") if isinstance(driver, dict) else ""
        if "snyk" in str(name).lower():
            return True
    return False


def parse(data: Any) -> str:
    """Normalize Snyk Open Source, Code, Container, or IaC JSON output."""
    roots = data if isinstance(data, list) else [data]
    lines = ["=== SNYK SECURITY SCAN ==="]
    total = sum(_finding_count(root) for root in roots if isinstance(root, dict))
    lines.append(f"Total Raw  : {total} findings")
    lines.append("")

    for root in roots:
        if not isinstance(root, dict):
            continue
        target = _target(root)
        product = _product(root)
        lines.append(f"--- {target} [{product}] ---")
        if "infrastructureAsCodeIssues" in root:
            _append_iac(lines, root.get("infrastructureAsCodeIssues") or [])
        elif isinstance(root.get("runs"), list):
            _append_code(lines, root["runs"])
        else:
            _append_vulnerabilities(lines, root.get("vulnerabilities") or [])
        lines.append("")

    return "\n".join(lines)


def _append_vulnerabilities(lines: list[str], vulnerabilities: Iterable[Any]) -> None:
    for finding in vulnerabilities:
        if not isinstance(finding, dict):
            continue
        severity = _severity(finding.get("severity"))
        issue_id = finding.get("id") or finding.get("issueId") or "SNYK-UNKNOWN"
        package = finding.get("packageName") or finding.get("name") or "unknown package"
        version = finding.get("version")
        title = finding.get("title") or finding.get("description") or ""
        lines.append(f"[{severity}] {issue_id}")
        lines.append(f"  Package  : {package}" + (f" {version}" if version else ""))
        if title:
            lines.append(f"  Summary  : {str(title).strip()[:300]}")
        fixed_in = finding.get("fixedIn")
        if fixed_in:
            lines.append(f"  Fixed in : {_format_list(fixed_in)}")
        upgrade_path = finding.get("upgradePath")
        if upgrade_path:
            lines.append(f"  Upgrade  : {_format_list(upgrade_path)}")
        identifiers = finding.get("identifiers") or {}
        cves = identifiers.get("CVE") if isinstance(identifiers, dict) else None
        if cves:
            lines.append(f"  CVE      : {_format_list(cves)}")
        cvss = finding.get("cvssScore")
        if cvss is not None:
            lines.append(f"  CVSS     : {cvss}")
        paths = finding.get("from")
        if paths:
            lines.append(f"  Path     : {' > '.join(str(item) for item in paths)}")
        references = _references(finding.get("references"))
        if references:
            lines.append(f"  Refs     : {references[0]}")
        lines.append("")


def _append_iac(lines: list[str], findings: Iterable[Any]) -> None:
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = _severity(finding.get("impact") or finding.get("severity"))
        issue_id = finding.get("id") or finding.get("key") or "SNYK-IAC-UNKNOWN"
        title = finding.get("title") or finding.get("issue") or "Infrastructure misconfiguration"
        path = finding.get("path") or "unknown"
        line = finding.get("lineNumber")
        lines.append(f"[{severity}] {issue_id}: {str(title).strip()[:300]}")
        lines.append(f"  Location : {path}" + (f":{line}" if line else ""))
        resource = finding.get("resourceName")
        if resource:
            lines.append(f"  Resource : {resource}")
        message = finding.get("msg") or finding.get("impact")
        if message:
            lines.append(f"  Detail   : {str(message).strip()[:300]}")
        remediation = finding.get("remediation")
        if remediation:
            lines.append(f"  Fix      : {str(remediation).strip()[:300]}")
        references = _references(finding.get("references"))
        if references:
            lines.append(f"  Refs     : {references[0]}")
        lines.append("")


def _append_code(lines: list[str], runs: Iterable[Any]) -> None:
    for run in runs:
        if not isinstance(run, dict):
            continue
        tool = run.get("tool") or {}
        driver = tool.get("driver") or {}
        rules = {
            rule.get("id"): rule
            for rule in driver.get("rules", [])
            if isinstance(rule, dict) and rule.get("id")
        }
        for finding in run.get("results") or []:
            if not isinstance(finding, dict):
                continue
            rule_id = finding.get("ruleId") or "SNYK-CODE-UNKNOWN"
            rule = rules.get(rule_id, {})
            message = (finding.get("message") or {}).get("text") or ""
            title = (
                (rule.get("shortDescription") or {}).get("text")
                or message
                or rule_id
            )
            properties = finding.get("properties") or {}
            severity_score = properties.get("security-severity")
            severity = (
                _severity(severity_score)
                if severity_score is not None
                else _severity(finding.get("level") or properties.get("severity"))
            )
            lines.append(f"[{severity}] {rule_id}: {str(title).strip()[:300]}")
            for location in finding.get("locations") or []:
                physical = (location or {}).get("physicalLocation") or {}
                artifact = physical.get("artifactLocation") or {}
                region = physical.get("region") or {}
                uri = artifact.get("uri") or "unknown"
                start_line = region.get("startLine")
                lines.append(
                    f"  Location : {uri}" + (f":{start_line}" if start_line else "")
                )
            if message and message.strip() != str(title).strip():
                lines.append(f"  Detail   : {message.strip()[:300]}")
            help_uri = rule.get("helpUri")
            if help_uri:
                lines.append(f"  Refs     : {help_uri}")
            lines.append("")


def _finding_count(root: dict[str, Any]) -> int:
    if "infrastructureAsCodeIssues" in root:
        return len(root.get("infrastructureAsCodeIssues") or [])
    if isinstance(root.get("runs"), list):
        return sum(
            len(run.get("results") or [])
            for run in root["runs"]
            if isinstance(run, dict)
        )
    return len(root.get("vulnerabilities") or [])


def _product(root: dict[str, Any]) -> str:
    if "infrastructureAsCodeIssues" in root:
        return "Snyk IaC"
    if isinstance(root.get("runs"), list):
        return "Snyk Code"
    if "docker" in root or root.get("image"):
        return "Snyk Container"
    return "Snyk Open Source"


def _target(root: dict[str, Any]) -> str:
    target = (
        root.get("displayTargetFile")
        or root.get("targetFile")
        or root.get("projectName")
        or root.get("image")
    )
    docker = root.get("docker")
    if not target and isinstance(docker, dict):
        target = docker.get("baseImage") or docker.get("image")
    return str(target or "unknown target")


def _severity(value: Any) -> str:
    if isinstance(value, (float, int)):
        if value >= 9:
            return "CRITICAL"
        if value >= 7:
            return "HIGH"
        if value >= 4:
            return "MEDIUM"
        if value > 0:
            return "LOW"
        return "INFO"
    if isinstance(value, str):
        try:
            return _severity(float(value))
        except ValueError:
            pass
    return _SEVERITY_MAP.get(str(value or "").lower(), "UNKNOWN")


def _references(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        str(item.get("url") or item.get("href"))
        if isinstance(item, dict)
        else str(item)
        for item in value
        if isinstance(item, (dict, str))
    ]


def _format_list(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)
