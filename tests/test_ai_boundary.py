from backend.ai.security_summary import AIInput, AIAnalysis


def test_ai_input_preserves_deterministic_values():
    data = AIInput(
        service_name="lab-hardened-api",
        technical_score=83,
        contextual_risk="HIGH",
        findings=[
            "DOCKER-008: Exposed ports",
            "DOCKER-011: Image configuration",
            "DOCKER-015: Sensitive environment configuration",
        ],
        context_summary=(
            "Criticality=CRITICAL; "
            "Exposure=INTERNET_FACING; "
            "Data sensitivity=SENSITIVE_PII."
        ),
    )

    assert data.technical_score == 83
    assert data.contextual_risk == "HIGH"


def test_ai_output_has_no_score_or_risk_fields():
    result = AIAnalysis(
        summary="Example interpretation",
        prioritized_recommendations=["Example recommendation"],
        referenced_evidence=["DOCKER-015"],
        confidence="high",
    )

    output = result.model_dump()

    assert "technical_score" not in output
    assert "contextual_risk" not in output
    assert "score" not in output
    assert "risk" not in output


def test_ai_analysis_schema_is_structured():
    result = AIAnalysis(
        summary="Security interpretation",
        prioritized_recommendations=[
            "Use a secrets manager",
            "Restrict exposed ports",
        ],
        referenced_evidence=[
            "DOCKER-015",
            "DOCKER-008",
        ],
        confidence="high",
    )

    assert result.summary
    assert len(result.prioritized_recommendations) == 2
    assert result.referenced_evidence == [
        "DOCKER-015",
        "DOCKER-008",
    ]
    assert result.confidence == "high"
