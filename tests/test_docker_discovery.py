import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.discovery.docker.docker_discovery import DockerDiscovery


@pytest.fixture(scope="module")
def discovery():
    return DockerDiscovery()


@pytest.fixture(scope="module")
def services(discovery):
    return discovery.discover_all()


def find_service(services, name):
    for s in services:
        if s.name == name:
            return s
    return None


def test_discovers_all_four_lab_services(services):
    names = {s.name for s in services}
    expected = {"lab-vuln-web", "lab-vuln-privileged", "lab-hardened-api", "lab-vuln-docker-socket"}
    assert expected.issubset(names), f"Missing services: {expected - names}"


def test_vuln_web_runs_as_root(services):
    s = find_service(services, "lab-vuln-web")
    assert s is not None
    assert s.user in (None, "", "root", "0")


def test_vuln_privileged_is_privileged(services):
    s = find_service(services, "lab-vuln-privileged")
    assert s is not None
    assert s.privileged is True
    assert s.network_mode == "host"


def test_hardened_api_is_nonroot_and_readonly(services):
    s = find_service(services, "lab-hardened-api")
    assert s is not None
    assert s.user not in (None, "", "root", "0")
    assert s.read_only_rootfs is True
    assert "ALL" in s.cap_drop


def test_vuln_docker_socket_has_socket_mount(services):
    s = find_service(services, "lab-vuln-docker-socket")
    assert s is not None
    socket_mounted = any(m.destination == "/var/run/docker.sock" for m in s.mounts)
    assert socket_mounted is True
