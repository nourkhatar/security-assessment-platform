from backend.discovery.kubernetes.kubernetes_discovery import (
    KubernetesDiscovery,
)


def _get_poc_service():
    discovery = KubernetesDiscovery(namespace="security-poc")
    services = discovery.discover_all()

    return next(
        service
        for service in services
        if service.name.endswith("/web")
    )


def test_kubernetes_poc_service_is_discovered():
    service = _get_poc_service()

    assert service.environment == "kubernetes"
    assert service.status == "running"
    assert service.image == "nginx:latest"


def test_kubernetes_security_properties_are_normalized():
    service = _get_poc_service()

    assert service.user == "0"
    assert service.privileged is False
    assert service.read_only_rootfs is False
    assert service.memory_limit_bytes is None
    assert service.nano_cpus is None
    assert service.network_mode == "pod-network"


def test_kubernetes_ports_and_environment_are_discovered():
    service = _get_poc_service()

    assert any(
        port.container_port == "80"
        for port in service.exposed_ports
    )

    assert service.env_vars["DEMO_SECRET"] == "poc-only-value"
