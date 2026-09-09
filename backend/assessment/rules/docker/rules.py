"""
Docker security rules — DOCKER-001 through DOCKER-015.

Each rule function takes a ServiceSnapshot and returns (status, evidence_dict).
Severity/weight assignments are frozen per §3.7 — do not change without flagging
MEMOIRE UPDATE REQUIRED.
"""
from backend.models.service import ServiceSnapshot
from backend.assessment.findings.finding import FindingStatus, Severity

RULE_CATALOG = {}  # populated by @register below


def register(rule_id, name, severity, recommendation):
    def decorator(func):
        RULE_CATALOG[rule_id] = {
            "func": func,
            "name": name,
            "severity": severity,
            "recommendation": recommendation,
        }
        return func
    return decorator


@register("DOCKER-001", "Non-root execution", Severity.HIGH,
          "Define a non-root USER in the Dockerfile or user: field in compose.")
def check_docker_001(s: ServiceSnapshot):
    is_root = s.user in (None, "", "root", "0")
    return (
        FindingStatus.FAIL if is_root else FindingStatus.PASS,
        {"inspected_field": "user", "value": s.user}
    )


@register("DOCKER-002", "Privileged mode", Severity.CRITICAL,
          "Remove privileged: true; grant only the specific capabilities required.")
def check_docker_002(s: ServiceSnapshot):
    return (
        FindingStatus.FAIL if s.privileged else FindingStatus.PASS,
        {"inspected_field": "privileged", "value": s.privileged}
    )


@register("DOCKER-003", "Linux capabilities", Severity.HIGH,
          "Drop all capabilities (cap_drop: ALL) and add back only what is strictly needed.")
def check_docker_003(s: ServiceSnapshot):
    all_dropped = "ALL" in s.cap_drop
    excessive_added = len(s.cap_add) > 0
    fail = excessive_added or not all_dropped
    return (
        FindingStatus.FAIL if fail else FindingStatus.PASS,
        {"inspected_field": "cap_add/cap_drop", "cap_add": s.cap_add, "cap_drop": s.cap_drop}
    )


@register("DOCKER-004", "Read-only filesystem", Severity.MEDIUM,
          "Set read_only: true and use tmpfs for any directories that need write access.")
def check_docker_004(s: ServiceSnapshot):
    return (
        FindingStatus.PASS if s.read_only_rootfs else FindingStatus.FAIL,
        {"inspected_field": "read_only_rootfs", "value": s.read_only_rootfs}
    )


@register("DOCKER-005", "Resource limits", Severity.LOW,
          "Set explicit memory and CPU limits to prevent resource exhaustion.")
def check_docker_005(s: ServiceSnapshot):
    has_limits = s.memory_limit_bytes is not None and s.nano_cpus is not None
    return (
        FindingStatus.PASS if has_limits else FindingStatus.FAIL,
        {"inspected_field": "memory_limit_bytes/nano_cpus",
         "memory_limit_bytes": s.memory_limit_bytes, "nano_cpus": s.nano_cpus}
    )


@register("DOCKER-006", "Host networking", Severity.CRITICAL,
          "Use the default bridge network or a custom network instead of host mode.")
def check_docker_006(s: ServiceSnapshot):
    return (
        FindingStatus.FAIL if s.network_mode == "host" else FindingStatus.PASS,
        {"inspected_field": "network_mode", "value": s.network_mode}
    )


@register("DOCKER-007", "Sensitive host mounts", Severity.CRITICAL,
          "Avoid mounting sensitive host paths (/, /etc, /var/run/docker.sock handled separately).")
def check_docker_007(s: ServiceSnapshot):
    sensitive_prefixes = ("/", "/etc", "/root", "/home")
    flagged = [m.model_dump() for m in s.mounts
               if m.source in sensitive_prefixes or m.source == "/"]
    return (
        FindingStatus.FAIL if flagged else FindingStatus.PASS,
        {"inspected_field": "mounts", "flagged_mounts": flagged}
    )


@register("DOCKER-008", "Exposed ports", Severity.MEDIUM,
          "Expose only the ports strictly required by the service.")
def check_docker_008(s: ServiceSnapshot):
    if len(s.exposed_ports) == 0:
        return (FindingStatus.NA, {"inspected_field": "exposed_ports", "value": []})
    # Baseline rule: any exposed port is flagged for review (severity/weight already low-medium).
    return (
        FindingStatus.FAIL,
        {"inspected_field": "exposed_ports",
         "value": [p.model_dump() for p in s.exposed_ports]}
    )


@register("DOCKER-009", "Docker socket exposure", Severity.CRITICAL,
          "Never mount /var/run/docker.sock into a container unless absolutely required and isolated.")
def check_docker_009(s: ServiceSnapshot):
    socket_mounted = any(m.destination == "/var/run/docker.sock" for m in s.mounts)
    return (
        FindingStatus.FAIL if socket_mounted else FindingStatus.PASS,
        {"inspected_field": "mounts", "socket_mounted": socket_mounted}
    )


@register("DOCKER-010", "Healthcheck", Severity.LOW,
          "Define a HEALTHCHECK instruction to enable orchestration-level failure detection.")
def check_docker_010(s: ServiceSnapshot):
    return (
        FindingStatus.PASS if s.healthcheck.configured else FindingStatus.FAIL,
        {"inspected_field": "healthcheck.configured", "value": s.healthcheck.configured}
    )


@register("DOCKER-011", "Image configuration", Severity.MEDIUM,
          "Pin images to a specific digest/tag rather than using 'latest' or an unpinned tag.")
def check_docker_011(s: ServiceSnapshot):
    unpinned = s.image.endswith(":latest") or (":" not in s.image and "@" not in s.image)
    return (
        FindingStatus.FAIL if unpinned else FindingStatus.PASS,
        {"inspected_field": "image", "value": s.image}
    )


@register("DOCKER-012", "Restart policy", Severity.LOW,
          "Set an explicit restart policy (e.g. unless-stopped) for production-relevant services.")
def check_docker_012(s: ServiceSnapshot):
    return (
        FindingStatus.PASS if s.restart_policy != "no" else FindingStatus.FAIL,
        {"inspected_field": "restart_policy", "value": s.restart_policy}
    )


@register("DOCKER-013", "Security options", Severity.MEDIUM,
          "Set security_opt: no-new-privileges:true at minimum.")
def check_docker_013(s: ServiceSnapshot):
    has_nnp = any("no-new-privileges" in opt for opt in s.security_opt)
    return (
        FindingStatus.PASS if has_nnp else FindingStatus.FAIL,
        {"inspected_field": "security_opt", "value": s.security_opt}
    )


@register("DOCKER-014", "Host PID/IPC modes", Severity.HIGH,
          "Avoid pid: host or ipc: host; use isolated namespaces unless explicitly required.")
def check_docker_014(s: ServiceSnapshot):
    fail = (s.pid_mode == "host") or (s.ipc_mode == "host")
    return (
        FindingStatus.FAIL if fail else FindingStatus.PASS,
        {"inspected_field": "pid_mode/ipc_mode", "pid_mode": s.pid_mode, "ipc_mode": s.ipc_mode}
    )


@register("DOCKER-015", "Sensitive environment configuration", Severity.HIGH,
          "Do not pass secrets/credentials via plaintext environment variables; use a secrets manager.")
def check_docker_015(s: ServiceSnapshot):
    sensitive_keywords = ("PASSWORD", "SECRET", "TOKEN", "KEY", "CREDENTIAL")
    flagged = {k: v for k, v in s.env_vars.items()
               if any(kw in k.upper() for kw in sensitive_keywords)}
    return (
        FindingStatus.FAIL if flagged else FindingStatus.PASS,
        {"inspected_field": "env_vars", "flagged_keys": list(flagged.keys())}
    )
