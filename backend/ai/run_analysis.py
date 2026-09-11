from backend.discovery.docker.docker_discovery import DockerDiscovery
from backend.assessment.engine.rule_engine import RuleEngine
from backend.assessment.findings.finding import FindingStatus
from backend.scoring.technical_score import calculate_technical_score
from backend.context.contextual_risk import calculate_contextual_risk
from backend.models.context import (
    ServiceContext,
    Criticality,
    Exposure,
    DataSensitivity,
)
from backend.ai.security_summary import AIInput
from backend.ai.gemini_client import analyze_security


def main() -> None:
    target_service = "lab-hardened-api"

    discovery = DockerDiscovery()
    services = discovery.discover_all()

    service = next(
        (s for s in services if s.name == target_service),
        None,
    )

    if service is None:
        raise RuntimeError(
            f"Service '{target_service}' was not found."
        )

    # 1. Deterministic rule evaluation
    engine = RuleEngine(run_id="phase8-ai-integration")
    findings = engine.evaluate(service)

    # 2. Deterministic technical score
    technical_score = calculate_technical_score(findings)

    # 3. Explicit contextual information
    context = ServiceContext(
        service=service.name,
        criticality=Criticality.CRITICAL,
        exposure=Exposure.INTERNET_FACING,
        data_sensitivity=DataSensitivity.SENSITIVE_PII,
    )

    # 4. Deterministic contextual risk
    contextual_risk = calculate_contextual_risk(
        technical_score.score,
        context,
    )

    failed_findings = [
        finding
        for finding in findings
        if finding.status == FindingStatus.FAIL
    ]

    findings_for_ai = [
        (
            f"{finding.rule_id}: {finding.rule_name}. "
            f"Severity={finding.severity.value}. "
            f"Recommendation={finding.recommendation}"
        )
        for finding in failed_findings
    ]

    context_summary = (
        f"Criticality={context.criticality.value}; "
        f"Exposure={context.exposure.value}; "
        f"Data sensitivity={context.data_sensitivity.value}; "
        f"Context weight={contextual_risk.context_weight}; "
        f"Context tier={contextual_risk.context_tier.value}."
    )

    # 5. Read-only AI interpretation
    ai_input = AIInput(
        service_name=service.name,
        technical_score=technical_score.score_rounded,
        contextual_risk=contextual_risk.contextual_risk_level.value,
        findings=findings_for_ai,
        context_summary=context_summary,
    )

    ai_result = analyze_security(ai_input)

    print("=== DETERMINISTIC ASSESSMENT ===")
    print(f"Service: {service.name}")
    print(f"Technical score: {technical_score.score_rounded}/100")
    print(
        "Failed rules: "
        f"{technical_score.failed_rules}/"
        f"{technical_score.applicable_rules}"
    )
    print(
        "Contextual risk: "
        f"{contextual_risk.contextual_risk_level.value}"
    )

    print("\n=== REAL FAILED FINDINGS ===")
    for finding in failed_findings:
        print(
            f"{finding.rule_id} "
            f"[{finding.severity.value}] "
            f"{finding.rule_name}"
        )

    print("\n=== AI INTERPRETATION ===")
    print(ai_result.summary)

    print("\nRECOMMENDATIONS:")
    for recommendation in ai_result.prioritized_recommendations:
        print(f"- {recommendation}")

    print("\nREFERENCED EVIDENCE:")
    for evidence in ai_result.referenced_evidence:
        print(f"- {evidence}")

    print("\nCONFIDENCE:")
    print(ai_result.confidence)

    print("\n=== INTEGRITY CHECK ===")
    print(
        "Technical score remains: "
        f"{technical_score.score_rounded}"
    )
    print(
        "Contextual risk remains: "
        f"{contextual_risk.contextual_risk_level.value}"
    )


if __name__ == "__main__":
    main()
