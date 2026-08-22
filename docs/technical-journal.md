# Technical Journal

## Entry 1 — 2026-08-22 — Phase 0: Environment Setup & Architecture

**Objective:** Establish a stable development environment and lock the system architecture
before any implementation begins.

**Implementation:**
- Evaluated Windows 11 native shell vs. Kali VM vs. WSL2 for the development environment.
- Selected WSL2 (existing Kali Linux distro) integrated with the already-installed Docker
  Desktop, avoiding nested virtualization that a separate VM would introduce.
- Verified Docker Engine 29.3.1, Docker Compose v5.1.1, Python 3.13.12, git 2.51.0/2.53.0,
  kubectl v1.34.1 already present in the environment.
- Installed: python3-pip, python3-venv, kind v0.27.0.
- Created project-local Python virtual environment (avoids Kali's PEP 668
  externally-managed-environment restriction on system-wide pip installs).
- Installed anthropic SDK v1.0.0 inside the venv; import verified.
- Configured git identity for commit history.
- Created project directory skeleton, .gitignore, requirements.txt, .env.example, README.md,
  and this architecture-overview.md.

**Problem:** Initial assumption was to build on Ubuntu WSL2 for a "clean" environment.
User already had Kali Linux as their default WSL2 distro (via WSL --status), and Docker
Desktop was already installed and functional.

**Solution:** Reassessed — Kali WSL2 is architecturally identical to Ubuntu WSL2 (same
kernel, same single virtualization layer, same Docker Desktop integration path); the
Debian/Kali userland has no negative bearing on Docker Engine internals being inspected
by the rule engine. Kept Kali as the environment rather than introducing an unnecessary
second distro.

**Result:** Working WSL2 (Kali) environment with Docker, kubectl, kind, Python venv, and
the anthropic SDK all verified functional. No blockers for Phase 1.

**Evidence:** Terminal output of `docker ps`, `docker info`, `kind version`, `pip --version`
(showing venv path), `python3 -c "import anthropic; print(anthropic.__version__)"`, and
git config confirmation — saved to evidence/screenshots/phase0/.

**Next step:** Phase 1 — Docker laboratory (vulnerable-by-design container targets for
the rule engine to assess).

**Thesis section affected:** Chapter 2 (Methodology/Architecture) — environment
justification, technology stack rationale, three-layer architectural separation.

## Entry 2 — 2026-08-22 — Phase 1: Docker Laboratory

**Objective:** Build a fixed set of Docker lab services with known, documented security
postures to serve as ground-truth input for the rule engine (Phase 3 onward).

**Implementation:**
- Built 4 lab services via infrastructure/docker/docker-compose.lab.yml:
  - vuln-web: custom Flask image, runs as root, no healthcheck, no resource limits,
    no restart policy — intentionally weak baseline.
  - vuln-privileged: stock nginx:1.27-alpine run with privileged: true, host networking,
    and a read-only bind mount of the host root filesystem — worst-case configuration.
  - hardened-api: custom Flask image, non-root user (uid 1001), read-only root filesystem,
    all capabilities dropped, no-new-privileges, resource limits, healthcheck, restart
    policy — best-case configuration.
  - vuln-docker-socket: alpine container with /var/run/docker.sock bind-mounted —
    isolated demonstration of a single critical container-escape-risk misconfiguration.
- Each service's compose definition is annotated inline with the DOCKER-XXX rule IDs it
  is designed to trigger (FAIL) or satisfy (PASS), forming a ground-truth table for later
  rule-engine validation.

**Problem:** Evidence capture commands were run from infrastructure/docker/ using a
relative evidence/ path, which created an unintended nested evidence/ folder inside
infrastructure/docker/ rather than writing to the project's root evidence/ directory.

**Solution:** Removed the accidental nested folder, created the correct
evidence/logs/phase1/ and evidence/screenshots/phase1/ under the project root, and
re-ran the capture commands using an explicit ../../evidence/logs/phase1/ relative path
from infrastructure/docker/.

**Result:** All 4 containers verified running (docker compose ps), hardened-api reaching
a healthy state, vuln-web and hardened-api both responding correctly over HTTP,
Privileged: true confirmed via docker inspect on vuln-privileged, and the
/var/run/docker.sock bind mount confirmed via docker inspect on vuln-docker-socket.

**Evidence:** evidence/logs/phase1/compose-ps.txt and four docker inspect JSON exports
(one per lab service), saved and committed.

**Next step:** Phase 2 — Docker discovery (enumerate the lab's running containers and
their full configuration via the Docker SDK for Python, as input to the Phase 3 rule
engine).

**Thesis section affected:** Chapter 3 (Implementation) — "Laboratory Design" subsection;
this entry's ground-truth table (which rule ID each service should trigger/pass) becomes
the reference used later to report rule-engine detection accuracy.
