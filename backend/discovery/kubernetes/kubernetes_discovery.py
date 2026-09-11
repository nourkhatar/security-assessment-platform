"""
Kubernetes discovery PoC.

Connects to the current Kubernetes context through the official Python client
and translates Pods into the existing platform-agnostic ServiceSnapshot model.

This module demonstrates extensibility of the discovery layer. It is not a
complete Kubernetes security assessment implementation.
"""

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

from backend.models.service import (
    ServiceSnapshot,
    MountInfo,
    PortInfo,
    HealthcheckInfo,
)


class KubernetesDiscoveryError(Exception):
    """Raised when the Kubernetes API cannot be reached or inspected."""


class KubernetesDiscovery:
    def __init__(self, namespace: str = "security-poc"):
        self.namespace = namespace

        try:
            config.load_kube_config()
            self.client = client.CoreV1Api()
            self.client.get_api_resources()
        except Exception as exc:
            raise KubernetesDiscoveryError(
                f"Could not connect to Kubernetes API: {exc}"
            ) from exc

    def discover_all(self) -> list[ServiceSnapshot]:
        try:
            pods = self.client.list_namespaced_pod(
                namespace=self.namespace
            ).items
        except ApiException as exc:
            raise KubernetesDiscoveryError(
                f"Could not list Pods in namespace "
                f"'{self.namespace}': {exc}"
            ) from exc

        snapshots = []

        for pod in pods:
            if pod.status.phase != "Running":
                continue

            for container in pod.spec.containers:
                snapshots.append(
                    self._to_snapshot(pod, container)
                )

        return snapshots

    def _to_snapshot(
        self,
        pod: client.V1Pod,
        container: client.V1Container,
    ) -> ServiceSnapshot:
        security_context = (
            container.security_context
            or client.V1SecurityContext()
        )

        capabilities = security_context.capabilities
        cap_add = list(capabilities.add or []) if capabilities else []
        cap_drop = list(capabilities.drop or []) if capabilities else []

        user = None
        if security_context.run_as_user is not None:
            user = str(security_context.run_as_user)

        privileged = bool(security_context.privileged or False)
        read_only_rootfs = bool(
            security_context.read_only_root_filesystem or False
        )

        memory_limit_bytes = self._memory_to_bytes(
            (container.resources.limits or {}).get("memory")
            if container.resources
            else None
        )

        nano_cpus = self._cpu_to_nano_cpus(
            (container.resources.limits or {}).get("cpu")
            if container.resources
            else None
        )

        ports = [
            PortInfo(
                container_port=str(port.container_port),
                host_port=(
                    str(port.host_port)
                    if port.host_port is not None
                    else None
                ),
                protocol=(port.protocol or "TCP").lower(),
            )
            for port in (container.ports or [])
        ]

        env_vars = {}
        for env in container.env or []:
            if env.value is not None:
                env_vars[env.name] = env.value
            elif env.value_from is not None:
                env_vars[env.name] = "<valueFrom>"

        mounts = []
        volume_types = self._volume_types(pod)

        for mount in container.volume_mounts or []:
            mounts.append(
                MountInfo(
                    source=mount.name,
                    destination=mount.mount_path,
                    mode="ro" if mount.read_only else "rw",
                    type=volume_types.get(
                        mount.name,
                        "kubernetes-volume",
                    ),
                )
            )

        probe = container.liveness_probe or container.readiness_probe
        healthcheck = HealthcheckInfo(
            configured=probe is not None,
            test=self._probe_description(probe),
            interval_seconds=(
                float(probe.period_seconds)
                if probe is not None
                and probe.period_seconds is not None
                else None
            ),
        )

        network_mode = (
            "host"
            if pod.spec.host_network
            else "pod-network"
        )

        security_opt = []
        if security_context.allow_privilege_escalation is False:
            security_opt.append("no-new-privileges")

        return ServiceSnapshot(
            service_id=str(pod.metadata.uid)[:12],
            name=f"{pod.metadata.name}/{container.name}",
            environment="kubernetes",
            image=container.image or "unknown",
            status=pod.status.phase.lower(),
            user=user,
            privileged=privileged,
            cap_add=cap_add,
            cap_drop=cap_drop,
            read_only_rootfs=read_only_rootfs,
            memory_limit_bytes=memory_limit_bytes,
            nano_cpus=nano_cpus,
            network_mode=network_mode,
            mounts=mounts,
            exposed_ports=ports,
            healthcheck=healthcheck,
            restart_policy=pod.spec.restart_policy or "Always",
            security_opt=security_opt,
            pid_mode=(
                "host"
                if pod.spec.host_pid
                else None
            ),
            ipc_mode=(
                "host"
                if pod.spec.host_ipc
                else None
            ),
            env_vars=env_vars,
            raw_labels=pod.metadata.labels or {},
        )

    @staticmethod
    def _volume_types(pod: client.V1Pod) -> dict[str, str]:
        result = {}

        for volume in pod.spec.volumes or []:
            volume_type = "kubernetes-volume"

            if volume.host_path is not None:
                volume_type = "hostPath"
            elif volume.secret is not None:
                volume_type = "secret"
            elif volume.config_map is not None:
                volume_type = "configMap"
            elif volume.persistent_volume_claim is not None:
                volume_type = "persistentVolumeClaim"
            elif volume.empty_dir is not None:
                volume_type = "emptyDir"

            result[volume.name] = volume_type

        return result

    @staticmethod
    def _probe_description(probe) -> str | None:
        if probe is None:
            return None

        if probe.http_get is not None:
            return (
                f"HTTP GET "
                f"{probe.http_get.path or '/'}:"
                f"{probe.http_get.port}"
            )

        if probe.tcp_socket is not None:
            return f"TCP {probe.tcp_socket.port}"

        if probe.exec is not None:
            return "EXEC " + " ".join(
                probe.exec.command or []
            )

        return "configured"

    @staticmethod
    def _memory_to_bytes(value: str | None) -> int | None:
        if not value:
            return None

        units = {
            "Ki": 1024,
            "Mi": 1024 ** 2,
            "Gi": 1024 ** 3,
            "Ti": 1024 ** 4,
        }

        for suffix, multiplier in units.items():
            if value.endswith(suffix):
                return int(float(value[:-len(suffix)]) * multiplier)

        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _cpu_to_nano_cpus(value: str | None) -> int | None:
        if not value:
            return None

        if value.endswith("m"):
            return int(float(value[:-1]) * 1_000_000)

        try:
            return int(float(value) * 1_000_000_000)
        except ValueError:
            return None


if __name__ == "__main__":
    discovery = KubernetesDiscovery()
    services = discovery.discover_all()

    print(
        f"Discovered {len(services)} Kubernetes "
        f"container(s):\n"
    )

    for service in services:
        print(f"--- {service.name} ---")
        print(service.model_dump_json(indent=2))
        print()
