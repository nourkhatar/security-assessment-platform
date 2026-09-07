"""
Normalized service snapshot model.

This is the contract between Discovery (Docker/Kubernetes) and everything downstream
(rule engine, scoring, context, AI). Discovery modules translate platform-specific
APIs into this shape; nothing downstream should need to know whether a service came
from Docker or Kubernetes.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class MountInfo(BaseModel):
    source: str
    destination: str
    mode: str          # "ro" or "rw"
    type: str           # "bind", "volume", etc.


class PortInfo(BaseModel):
    container_port: str
    host_port: Optional[str] = None
    protocol: str = "tcp"


class HealthcheckInfo(BaseModel):
    configured: bool
    test: Optional[str] = None
    interval_seconds: Optional[float] = None


class ServiceSnapshot(BaseModel):
    """Normalized, platform-agnostic snapshot of a running containerized service."""

    service_id: str
    name: str
    environment: str = "docker"
    image: str
    status: str

    user: Optional[str] = None
    privileged: bool = False
    cap_add: list[str] = Field(default_factory=list)
    cap_drop: list[str] = Field(default_factory=list)
    read_only_rootfs: bool = False
    memory_limit_bytes: Optional[int] = None
    nano_cpus: Optional[int] = None
    network_mode: str = "default"
    mounts: list[MountInfo] = Field(default_factory=list)
    exposed_ports: list[PortInfo] = Field(default_factory=list)
    healthcheck: HealthcheckInfo = Field(default_factory=lambda: HealthcheckInfo(configured=False))
    restart_policy: str = "no"
    security_opt: list[str] = Field(default_factory=list)
    pid_mode: Optional[str] = None
    ipc_mode: Optional[str] = None
    env_vars: dict[str, str] = Field(default_factory=dict)

    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_labels: dict[str, str] = Field(default_factory=dict)
