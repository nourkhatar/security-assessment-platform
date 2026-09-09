"""
Deterministic contextual risk model — frozen §3.8.

Context Weight = criticality_points + exposure_points + data_sensitivity_points
Context Tier <- Context Weight (lookup)
Technical Tier <- Technical Score (lookup)
rank_sum = rank(Technical Tier) + rank(Context Tier)
Contextual Risk Level <- rank_sum (lookup)

Categorical output only. No AI involvement. Pure function of
(technical_score, ServiceContext).
"""
from enum import Enum
from pydantic import BaseModel

from backend.models.context import (
    ServiceContext, CRITICALITY_POINTS, EXPOSURE_POINTS, DATA_SENSITIVITY_POINTS
)


class Tier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


TIER_RANK = {Tier.LOW: 0, Tier.MEDIUM: 1, Tier.HIGH: 2, Tier.CRITICAL: 3}


class ContextualRisk(BaseModel):
    service: str
    technical_score: float
    technical_tier: Tier
    context_weight: int
    context_tier: Tier
    rank_sum: int
    contextual_risk_level: Tier


def _context_tier(context_weight: int) -> Tier:
    if context_weight <= 1:
        return Tier.LOW
    elif context_weight <= 4:
        return Tier.MEDIUM
    elif context_weight <= 6:
        return Tier.HIGH
    else:
        return Tier.CRITICAL


def _technical_tier(technical_score: float) -> Tier:
    if technical_score >= 80:
        return Tier.LOW
    elif technical_score >= 60:
        return Tier.MEDIUM
    elif technical_score >= 40:
        return Tier.HIGH
    else:
        return Tier.CRITICAL


def _risk_from_rank_sum(rank_sum: int) -> Tier:
    if rank_sum == 0:
        return Tier.LOW
    elif rank_sum <= 2:
        return Tier.MEDIUM
    elif rank_sum <= 4:
        return Tier.HIGH
    else:
        return Tier.CRITICAL


def calculate_contextual_risk(technical_score: float, context: ServiceContext) -> ContextualRisk:
    context_weight = (
        CRITICALITY_POINTS[context.criticality]
        + EXPOSURE_POINTS[context.exposure]
        + DATA_SENSITIVITY_POINTS[context.data_sensitivity]
    )
    context_tier = _context_tier(context_weight)
    technical_tier = _technical_tier(technical_score)
    rank_sum = TIER_RANK[technical_tier] + TIER_RANK[context_tier]
    risk_level = _risk_from_rank_sum(rank_sum)

    return ContextualRisk(
        service=context.service,
        technical_score=technical_score,
        technical_tier=technical_tier,
        context_weight=context_weight,
        context_tier=context_tier,
        rank_sum=rank_sum,
        contextual_risk_level=risk_level,
    )
