"""
Structured security finding — the deterministic output of one rule evaluation
against one service.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class FindingStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NA = "N/A"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Frozen weight table — §3.7. Do not modify without a MEMOIRE UPDATE REQUIRED flag.
SEVERITY_WEIGHT = {
    Severity.CRITICAL: 10,
    Severity.HIGH: 7,
    Severity.MEDIUM: 4,
    Severity.LOW: 1,
}


class Finding(BaseModel):
    finding_id: str
    run_id: str
    rule_id: str
    rule_name: str
    service: str
    environment: str = "docker"
    status: FindingStatus
    severity: Severity
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommendation: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)
