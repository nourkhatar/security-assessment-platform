import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.models.context import ServiceContext, Criticality, Exposure, DataSensitivity
from backend.context.contextual_risk import calculate_contextual_risk, Tier


def make_context(criticality, exposure, data_sensitivity):
    return ServiceContext(
        service="test-service",
        criticality=criticality,
        exposure=exposure,
        data_sensitivity=data_sensitivity,
    )


# --- Context Weight boundary tests ---

def test_context_weight_zero_is_low_tier():
    ctx = make_context(Criticality.LOW, Exposure.INTERNAL_ONLY, DataSensitivity.NONE)
    result = calculate_contextual_risk(90, ctx)
    assert result.context_weight == 0
    assert result.context_tier == Tier.LOW


def test_context_weight_max_is_critical_tier():
    ctx = make_context(Criticality.CRITICAL, Exposure.INTERNET_FACING, DataSensitivity.SENSITIVE_CREDENTIALS)
    result = calculate_contextual_risk(90, ctx)
    assert result.context_weight == 8
    assert result.context_tier == Tier.CRITICAL


# --- Technical tier boundary tests ---

def test_technical_score_80_is_low_tier():
    ctx = make_context(Criticality.LOW, Exposure.INTERNAL_ONLY, DataSensitivity.NONE)
    result = calculate_contextual_risk(80, ctx)
    assert result.technical_tier == Tier.LOW


def test_technical_score_79_is_medium_tier():
    ctx = make_context(Criticality.LOW, Exposure.INTERNAL_ONLY, DataSensitivity.NONE)
    result = calculate_contextual_risk(79, ctx)
    assert result.technical_tier == Tier.MEDIUM


def test_technical_score_39_is_critical_tier():
    ctx = make_context(Criticality.LOW, Exposure.INTERNAL_ONLY, DataSensitivity.NONE)
    result = calculate_contextual_risk(39, ctx)
    assert result.technical_tier == Tier.CRITICAL


# --- The core experiment, as an assertion ---

def test_same_technical_score_different_context_different_risk():
    context_a = make_context(Criticality.LOW, Exposure.INTERNAL_ONLY, DataSensitivity.NONE)
    context_b = make_context(Criticality.CRITICAL, Exposure.INTERNET_FACING, DataSensitivity.SENSITIVE_PII)

    risk_a = calculate_contextual_risk(83, context_a)
    risk_b = calculate_contextual_risk(83, context_b)

    assert risk_a.technical_score == risk_b.technical_score  # same input score
    assert risk_a.contextual_risk_level == Tier.LOW
    assert risk_b.contextual_risk_level == Tier.HIGH
    assert risk_a.contextual_risk_level != risk_b.contextual_risk_level  # the actual claim
