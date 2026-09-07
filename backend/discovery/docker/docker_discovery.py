"""
Docker discovery module.

Connects to the local Docker Engine via the Docker SDK for Python and produces
normalized ServiceSnapshot objects for every running container.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import docker
from docker.errors import DockerException

from backend.models.service import ServiceSnapshot, MountInfo, PortInfo, HealthcheckInfo


class DockerDiscoveryError(Exception):
    """Raised when the Docker daemon cannot be reached or a container cannot be inspected."""


class DockerDiscovery:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
        except DockerException as e:
            raise DockerDiscoveryError(f"Could not connect to Docker daemon: {e}")

    def discover_all(self, include_stopped: bool = False) -> list[ServiceSnapshot]:
        containers = self.client.containers.list(all=include_stopped)
        snapshots = []
        for c in containers:
            try:
                snapshots.append(self._to_snapshot(c))
            except Exception as e:
                print(f"[docker_discovery] WARNING: failed to inspect {c.name}: {e}", file=sys.stderr)
        return snapshots

    def _to_snapshot(self, container) -> ServiceSnapshot:
        raw = container.attrs
        config = raw.get("Config", {})
        host_config = raw.get("HostConfig", {})

        user = config.get("User") or None
        privileged = bool(host_config.get("Privileged", False))
        cap_add = host_config.get("CapAdd") or []
        cap_drop = host_config.get("CapDrop") or []
        read_only_rootfs = bool(host_config.get("ReadonlyRootfs", False))

        memory_limit = host_config.get("Memory") or None
        if memory_limit == 0:
            memory_limit = None
        nano_cpus = host_config.get("NanoCpus") or None
        if nano_cpus == 0:
            nano_cpus = None

        network_mode = host_config.get("NetworkMode", "default")

        mounts = []
        for m in raw.get("Mounts", []):
            mounts.append(MountInfo(
                source=m.get("Source", ""),
                destination=m.get("Destination", ""),
                mode="ro" if not m.get("RW", True) else "rw",
                type=m.get("Type", "unknown"),
            ))

        exposed_ports = []
        port_bindings = host_config.get("PortBindings") or {}
        for container_port, bindings in port_bindings.items():
            proto = "tcp"
            cport = container_port
            if "/" in container_port:
                cport, proto = container_port.split("/")
            if bindings:
                for b in bindings:
                    exposed_ports.append(PortInfo(
                        container_port=cport,
                        host_port=b.get("HostPort"),
                        protocol=proto,
                    ))
            else:
                exposed_ports.append(PortInfo(container_port=cport, host_port=None, protocol=proto))

        hc = config.get("Healthcheck")
        if hc and hc.get("Test"):
            healthcheck = HealthcheckInfo(
                configured=True,
                test=" ".join(hc.get("Test", [])) if isinstance(hc.get("Test"), list) else str(hc.get("Test")),
                interval_seconds=(hc.get("Interval", 0) / 1_000_000_000) if hc.get("Interval") else None,
            )
        else:
            healthcheck = HealthcheckInfo(configured=False)

        restart_policy = (host_config.get("RestartPolicy") or {}).get("Name", "no")
        security_opt = host_config.get("SecurityOpt") or []
        pid_mode = host_config.get("PidMode") or None
        ipc_mode = host_config.get("IpcMode") or None

        env_list = config.get("Env") or []
        env_vars = {}
        for item in env_list:
            if "=" in item:
                k, v = item.split("=", 1)
                env_vars[k] = v

        return ServiceSnapshot(
            service_id=raw.get("Id", "")[:12],
            name=container.name,
            environment="docker",
            image=config.get("Image", "unknown"),
            status=raw.get("State", {}).get("Status", "unknown"),
            user=user,
            privileged=privileged,
            cap_add=cap_add,
            cap_drop=cap_drop,
            read_only_rootfs=read_only_rootfs,
            memory_limit_bytes=memory_limit,
            nano_cpus=nano_cpus,
            network_mode=network_mode,
            mounts=mounts,
            exposed_ports=exposed_ports,
            healthcheck=healthcheck,
            restart_policy=restart_policy,
            security_opt=security_opt,
            pid_mode=pid_mode,
            ipc_mode=ipc_mode,
            env_vars=env_vars,
            raw_labels=config.get("Labels") or {},
        )


if __name__ == "__main__":
    discovery = DockerDiscovery()
    services = discovery.discover_all()
    print(f"Discovered {len(services)} running container(s):\n")
    for s in services:
        print(f"--- {s.name} ---")
        print(s.model_dump_json(indent=2))
        print()
