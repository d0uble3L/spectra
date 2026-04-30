from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ScanMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_raw_findings: int = 0
    after_dedup: int = 0
    scan_timestamp: Optional[str] = None


class Finding(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    title: str
    description: str
    affected_component: str
    cvss_score: Optional[float] = None
    exploitability: Literal["Immediate", "Requires Access", "Complex", "Theoretical"] = "Complex"
    remediation: str
    references: list[str] = Field(default_factory=list)


class AttackChain(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    description: str
    finding_ids: list[str] = Field(default_factory=list)


class FindingsBySeverity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    CRITICAL: int = 0
    HIGH: int = 0
    MEDIUM: int = 0
    LOW: int = 0
    INFO: int = 0

    @property
    def total(self) -> int:
        return self.CRITICAL + self.HIGH + self.MEDIUM + self.LOW + self.INFO


class AnalysisReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    executive_summary: str
    overall_risk_score: int = Field(ge=0, le=100)
    risk_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    scanner_type: str = "Unknown"
    scan_metadata: ScanMetadata = Field(default_factory=ScanMetadata)
    findings_by_severity: FindingsBySeverity = Field(default_factory=FindingsBySeverity)
    findings: list[Finding] = Field(default_factory=list)
    attack_chains: list[AttackChain] = Field(default_factory=list)
    immediate_actions: list[str] = Field(default_factory=list)
    strategic_recommendations: list[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
