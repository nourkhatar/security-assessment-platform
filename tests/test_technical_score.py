import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.discovery.docker.docker_discovery import DockerDiscovery
from backend.assessment.engine.rule_engine import RuleEngine
from backend.scoring.technical_score import calculate_technical_score


EXPECTED_SCORES = {
    "lab-vuln-privileged": 34,
    "lab-vuln-docker-socket": 58,
    "lab-hardened-api": 83,
    "lab-vuln-web": 54,
}


@pytest.fixture(scope="module")
def scores():
    discovery = DockerDiscovery()
    services = discovery.discover_all()
    engine = RuleEngine(run_id="pytest-phase4")
    result = {}
    for s in services:
        findings = engine.evaluate(s)
        result[s.name] = calculate_technical_score(findings)
    return result


@pytest.mark.parametrize("service_name,expected", list(EXPECTED_SCORES.items()))
def test_score_matches_expected(scores, service_name, expected):
    assert service_name in scores, f"{service_name} not discovered"
    assert scores[service_name].score_rounded == expected, (
        f"{service_name}: expected {expected}, got {scores[service_name].score_rounded}"
    )


def test_score_reproducibility(scores):
    """Re-running the calculation on the same findings must yield an identical score."""
    discovery = DockerDiscovery()
    services = discovery.discover_all()
    engine = RuleEngine(run_id="pytest-phase4-repeat")
    for s in services:
        findings = engine.evaluate(s)
        recomputed = calculate_technical_score(findings)
        assert recomputed.score_rounded == scores[s.name].score_rounded, (
            f"{s.name}: score not reproducible across runs"
        )


def test_score_range_is_valid(scores):
    for service_name, ts in scores.items():
        assert 0 <= ts.score <= 100, f"{service_name}: score {ts.score} out of range"
