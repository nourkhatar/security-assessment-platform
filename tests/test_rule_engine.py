import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.discovery.docker.docker_discovery import DockerDiscovery
from backend.assessment.engine.rule_engine import RuleEngine
from backend.assessment.findings.finding import FindingStatus


@pytest.fixture(scope="module")
def all_findings():
    discovery = DockerDiscovery()
    services = discovery.discover_all()
    engine = RuleEngine(run_id="pytest-phase3")
    return {s.name: {f.rule_id: f.status for f in engine.evaluate(s)} for s in services}


EXPECTED = {
    "lab-vuln-privileged": {
        "DOCKER-001": FindingStatus.FAIL, "DOCKER-002": FindingStatus.FAIL,
        "DOCKER-003": FindingStatus.FAIL, "DOCKER-004": FindingStatus.FAIL,
        "DOCKER-005": FindingStatus.FAIL, "DOCKER-006": FindingStatus.FAIL,
        "DOCKER-007": FindingStatus.FAIL, "DOCKER-008": FindingStatus.NA,
        "DOCKER-009": FindingStatus.PASS, "DOCKER-010": FindingStatus.FAIL,
        "DOCKER-011": FindingStatus.PASS, "DOCKER-012": FindingStatus.FAIL,
        "DOCKER-013": FindingStatus.FAIL, "DOCKER-014": FindingStatus.PASS,
        "DOCKER-015": FindingStatus.PASS,
    },
    "lab-vuln-docker-socket": {
        "DOCKER-001": FindingStatus.FAIL, "DOCKER-002": FindingStatus.PASS,
        "DOCKER-003": FindingStatus.FAIL, "DOCKER-004": FindingStatus.FAIL,
        "DOCKER-005": FindingStatus.FAIL, "DOCKER-006": FindingStatus.PASS,
        "DOCKER-007": FindingStatus.PASS, "DOCKER-008": FindingStatus.NA,
        "DOCKER-009": FindingStatus.FAIL, "DOCKER-010": FindingStatus.FAIL,
        "DOCKER-011": FindingStatus.PASS, "DOCKER-012": FindingStatus.FAIL,
        "DOCKER-013": FindingStatus.FAIL, "DOCKER-014": FindingStatus.PASS,
        "DOCKER-015": FindingStatus.PASS,
    },
    "lab-hardened-api": {
        "DOCKER-001": FindingStatus.PASS, "DOCKER-002": FindingStatus.PASS,
        "DOCKER-003": FindingStatus.PASS, "DOCKER-004": FindingStatus.PASS,
        "DOCKER-005": FindingStatus.PASS, "DOCKER-006": FindingStatus.PASS,
        "DOCKER-007": FindingStatus.PASS,
        "DOCKER-008": FindingStatus.FAIL,   # known limitation: any exposed port fails (§5.8)
        "DOCKER-009": FindingStatus.PASS, "DOCKER-010": FindingStatus.PASS,
        "DOCKER-011": FindingStatus.FAIL,   # untagged locally-built image
        "DOCKER-012": FindingStatus.PASS, "DOCKER-013": FindingStatus.PASS,
        "DOCKER-014": FindingStatus.PASS,
        "DOCKER-015": FindingStatus.FAIL,   # known false positive: GPG_KEY (§5.8)
    },
    "lab-vuln-web": {
        "DOCKER-001": FindingStatus.FAIL, "DOCKER-002": FindingStatus.PASS,
        "DOCKER-003": FindingStatus.FAIL, "DOCKER-004": FindingStatus.FAIL,
        "DOCKER-005": FindingStatus.FAIL, "DOCKER-006": FindingStatus.PASS,
        "DOCKER-007": FindingStatus.PASS, "DOCKER-008": FindingStatus.FAIL,
        "DOCKER-009": FindingStatus.PASS, "DOCKER-010": FindingStatus.FAIL,
        "DOCKER-011": FindingStatus.FAIL, "DOCKER-012": FindingStatus.FAIL,
        "DOCKER-013": FindingStatus.FAIL, "DOCKER-014": FindingStatus.PASS,
        "DOCKER-015": FindingStatus.FAIL,   # known false positive: GPG_KEY (§5.8)
    },
}


@pytest.mark.parametrize("service_name", list(EXPECTED.keys()))
def test_service_verdicts_match_ground_truth(all_findings, service_name):
    assert service_name in all_findings, f"{service_name} not discovered"
    actual = all_findings[service_name]
    expected = EXPECTED[service_name]
    assert actual == expected, (
        f"Mismatch for {service_name}: "
        f"{ {k: v for k, v in actual.items() if expected.get(k) != v} }"
    )
