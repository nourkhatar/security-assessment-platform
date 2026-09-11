from typing import List, Literal
from pydantic import BaseModel, Field


class AIInput(BaseModel):
    service_name: str
    technical_score: int = Field(ge=0, le=100)
    contextual_risk: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    findings: List[str]
    context_summary: str


class AIAnalysis(BaseModel):
    summary: str
    prioritized_recommendations: List[str]
    referenced_evidence: List[str]
    confidence: Literal["low", "medium", "high"]


def build_security_prompt(data: AIInput) -> str:
    findings_text = "\n".join(
        f"- {finding}" for finding in data.findings
    )

    return f"""
You are a read-only cybersecurity analysis assistant.

Your role is to interpret deterministic security assessment results.
You MUST NOT recalculate, modify, override, or contradict the supplied
technical score or contextual risk level.

Service: {data.service_name}
Technical score: {data.technical_score}/100
Contextual risk: {data.contextual_risk}

Context:
{data.context_summary}

Deterministic findings:
{findings_text}

Produce:
1. A concise security summary.
2. Prioritized remediation recommendations based only on the supplied findings.
3. The identifiers of the findings used as evidence.
4. A confidence level: low, medium, or high.

Do not invent vulnerabilities or evidence that are not present above.
""".strip()
