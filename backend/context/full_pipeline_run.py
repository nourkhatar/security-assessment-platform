"""
Consolidated deterministic pipeline run: Discovery -> Rules -> Technical Score
-> Contextual Risk, across all lab services with assigned contexts. Produces
the master evidence table for Chapter 5, §5.2-§5.3.
"""
from backend.discovery.docker.docker_discovery import DockerDiscovery
from backend.assessment.engine.rule_engine import RuleEngine
from backend.scoring.technical_score import calculate_technical_score
from backend.models.context import ServiceContext, Criticality, Exposure, DataSensitivity
from backend.context.contextual_risk import calculate_contextual_risk

CONTEXT_ASSIGNMENTS = {
    "lab-vuln-web": ServiceContext(
        service="lab-vuln-web", criticality=Criticality.LOW,
        exposure=Exposure.INTERNAL_ONLY, data_sensitivity=DataSensitivity.NONE,
    ),
    "lab-vuln-privileged": ServiceContext(
        service="lab-vuln-privileged", criticality=Criticality.MEDIUM,
        exposure=Exposure.INTERNAL_NETWORK, data_sensitivity=DataSensitivity.INTERNAL,
    ),
    "lab-vuln-docker-socket": ServiceContext(
        service="lab-vuln-docker-socket", criticality=Criticality.HIGH,
        exposure=Exposure.INTERNAL_NETWORK, data_sensitivity=DataSensitivity.INTERNAL,
    ),
    "lab-hardened-api": ServiceContext(
        service="lab-hardened-api (scenario A)", criticality=Criticality.LOW,
        exposure=Exposure.INTERNAL_ONLY, data_sensitivity=DataSensitivity.NONE,
    ),
}

HARDENED_API_SCENARIO_B = ServiceContext(
    service="lab-hardened-api (scenario B)", criticality=Criticality.CRITICAL,
    exposure=Exposure.INTERNET_FACING, data_sensitivity=DataSensitivity.SENSITIVE_PII,
)


def main():
    discovery = DockerDiscovery()
    services = discovery.discover_all()
    engine = RuleEngine(run_id="phase-consolidated-run")

    rows = []
    for s in services:
        findings = engine.evaluate(s)
        ts = calculate_technical_score(findings)
        ctx = CONTEXT_ASSIGNMENTS[s.name]
        risk = calculate_contextual_risk(ts.score, ctx)
        rows.append((ctx.service, ts.score_rounded, risk.technical_tier.value,
                     risk.context_tier.value, risk.contextual_risk_level.value))

        if s.name == "lab-hardened-api":
            risk_b = calculate_contextual_risk(ts.score, HARDENED_API_SCENARIO_B)
            rows.append((HARDENED_API_SCENARIO_B.service, ts.score_rounded,
                         risk_b.technical_tier.value, risk_b.context_tier.value,
                         risk_b.contextual_risk_level.value))

    print(f"{'Service':<40} {'Score':>6} {'TechTier':>10} {'CtxTier':>10} {'Risk':>10}")
    for r in rows:
        print(f"{r[0]:<40} {r[1]:>6} {r[2]:>10} {r[3]:>10} {r[4]:>10}")


if __name__ == "__main__":
    main()
