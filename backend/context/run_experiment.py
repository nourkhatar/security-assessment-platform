"""
Chapter 5 core experiment: identical technical score, different service
context, different contextual risk. Uses the REAL, previously-verified
technical score for lab-hardened-api (Phase 4), not a hypothetical value.
"""
from backend.discovery.docker.docker_discovery import DockerDiscovery
from backend.assessment.engine.rule_engine import RuleEngine
from backend.scoring.technical_score import calculate_technical_score
from backend.models.context import ServiceContext, Criticality, Exposure, DataSensitivity
from backend.context.contextual_risk import calculate_contextual_risk


def main():
    discovery = DockerDiscovery()
    services = discovery.discover_all()
    engine = RuleEngine(run_id="phase5-6-experiment")

    target = next((s for s in services if s.name == "lab-hardened-api"), None)
    if target is None:
        raise RuntimeError("lab-hardened-api not found — is the lab running?")

    findings = engine.evaluate(target)
    ts = calculate_technical_score(findings)
    print(f"Real technical score for {ts.service}: {ts.score_rounded}\n")

    context_a = ServiceContext(
        service="hardened-api (scenario A: internal tool)",
        criticality=Criticality.LOW,
        exposure=Exposure.INTERNAL_ONLY,
        data_sensitivity=DataSensitivity.NONE,
    )
    context_b = ServiceContext(
        service="hardened-api (scenario B: public auth service)",
        criticality=Criticality.CRITICAL,
        exposure=Exposure.INTERNET_FACING,
        data_sensitivity=DataSensitivity.SENSITIVE_PII,
    )

    risk_a = calculate_contextual_risk(ts.score, context_a)
    risk_b = calculate_contextual_risk(ts.score, context_b)

    for label, risk in [("Scenario A (internal, low criticality)", risk_a),
                         ("Scenario B (internet-facing, critical, PII)", risk_b)]:
        print(f"--- {label} ---")
        print(f"  Technical Score:     {risk.technical_score} (Tier: {risk.technical_tier.value})")
        print(f"  Context Weight:      {risk.context_weight} (Tier: {risk.context_tier.value})")
        print(f"  rank_sum:            {risk.rank_sum}")
        print(f"  Contextual Risk:     {risk.contextual_risk_level.value}")
        print()


if __name__ == "__main__":
    main()
