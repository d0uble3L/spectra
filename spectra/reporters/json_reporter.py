from __future__ import annotations

import json

from ..models import AnalysisReport


def render(report: AnalysisReport) -> str:
    data = report.model_dump(mode="json")
    return json.dumps(data, indent=2, default=str)
