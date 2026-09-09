"""
Deterministic technical scoring — implements the frozen §3.7 formula.

Score = 100 - (sum of weights of FAIL applicable rules / sum of weights of all
applicable rules) * 100

Only DOCKER-008 may produce an N/A verdict (excluded from numerator and
denominator). Pure function of Finding objects — no AI involvement.
"""
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.assessment.findings.finding import Finding, FindingStatus, SEVERITY_WEIGHT


class TechnicalScore(BaseModel):
    service: str
    run_id: str
    score: float
    score_rounded: int
    applicable_rules: int
    failed_rules: int
    max_deduction: int
    actual_deduction: int
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def calculate_technical_score(findings: list[Finding]) -> TechnicalScore:
    if not findings:
        raise ValueError("Cannot calculate a technical score from an empty findings list.")

    service = findings[0].service
    run_id = findings[0].run_id

    applicable = [f for f in findings if f.status != FindingStatus.NA]
    failed = [f for f in applicable if f.status == FindingStatus.FAIL]

    max_deduction = sum(SEVERITY_WEIGHT[f.severity] for f in applicable)
    actual_deduction = sum(SEVERITY_WEIGHT[f.severity] for f in failed)

    if max_deduction == 0:
        score = 100.0
    else:
        score = 100.0 - (actual_deduction / max_deduction) * 100.0

    return TechnicalScore(
        service=service,
        run_id=run_id,
        score=score,
        score_rounded=round(score),
        applicable_rules=len(applicable),
        failed_rules=len(failed),
        max_deduction=max_deduction,
        actual_deduction=actual_deduction,
    )


if __name__ == "__main__":
    from backend.discovery.docker.docker_discovery import DockerDiscovery
    from backend.assessment.engine.rule_engine import RuleEngine

    discovery = DockerDiscovery()
    services = discovery.discover_all()
    engine = RuleEngine(run_id="manual-smoke-test-phase4")

    print(f"{'Service':<25} {'Score':>6} {'Failed/Applicable':>20}")
    for s in services:
        findings = engine.evaluate(s)
        ts = calculate_technical_score(findings)
        print(f"{ts.service:<25} {ts.score_rounded:>6} {ts.failed_rules}/{ts.applicable_rules:>17}")
