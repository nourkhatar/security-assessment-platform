"""
Rule engine — executes the full rule catalog against a ServiceSnapshot,
producing a list of Finding objects. Pure, deterministic; no AI involvement.
"""
import uuid
from backend.models.service import ServiceSnapshot
from backend.assessment.rules.docker.rules import RULE_CATALOG
from backend.assessment.findings.finding import Finding, FindingStatus


class RuleEngine:
    def __init__(self, run_id: str):
        self.run_id = run_id

    def evaluate(self, snapshot: ServiceSnapshot) -> list[Finding]:
        findings = []
        for rule_id, rule_def in RULE_CATALOG.items():
            status, evidence = rule_def["func"](snapshot)
            findings.append(Finding(
                finding_id=str(uuid.uuid4())[:8],
                run_id=self.run_id,
                rule_id=rule_id,
                rule_name=rule_def["name"],
                service=snapshot.name,
                environment=snapshot.environment,
                status=status,
                severity=rule_def["severity"],
                evidence=evidence,
                recommendation=rule_def["recommendation"],
                metadata={"image": snapshot.image},
            ))
        return findings


if __name__ == "__main__":
    import sys
    import json
    sys.path.insert(0, ".")
    from backend.discovery.docker.docker_discovery import DockerDiscovery

    discovery = DockerDiscovery()
    services = discovery.discover_all()
    engine = RuleEngine(run_id="manual-smoke-test")

    for s in services:
        print(f"\n=== {s.name} ===")
        findings = engine.evaluate(s)
        for f in findings:
            print(f"  {f.rule_id} [{f.severity.value}] -> {f.status.value}")
