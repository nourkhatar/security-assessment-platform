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

## Entry 3 — 7 September 2026 — Phase 2: Docker Discovery (completed and verified)

**Objective:** Implement and verify a Docker discovery module producing normalized
ServiceSnapshot objects from the running lab.

**Implementation:**
- backend/models/service.py: ServiceSnapshot Pydantic model with MountInfo, PortInfo,
  HealthcheckInfo sub-models, covering all fields needed by the 15 planned rules.
- backend/discovery/docker/docker_discovery.py: DockerDiscovery class using the Docker
  SDK for Python (docker.from_env()), producing a list of ServiceSnapshot from all
  running containers.
- tests/test_docker_discovery.py: 5 pytest tests validating discovery output against
  the Phase 1 lab's known ground truth.

**Problem 1:** Files were initially instructed but never actually created on disk —
confirmed via a diagnostic (ls + git status) showing empty directories, despite an
earlier handoff report having assumed otherwise. Corrected by explicitly recreating
all files and verifying their presence and content before proceeding further.

**Problem 2:** `pip install -r requirements.txt` initially failed with Kali's PEP 668
"externally-managed-environment" error. Root cause: the project venv was not active in
that shell session. Resolved by re-activating (`source venv/bin/activate`) before
reinstalling; this same root cause (forgetting to activate the venv in a fresh WSL
terminal) recurred twice more during this phase (once for the discovery script, once
for pytest) and was resolved the same way each time.

**Problem 3:** Running the discovery script failed with a Docker daemon connection
error (`FileNotFoundError` on `/var/run/docker.sock`). Root cause: Docker Desktop was
not running on the Windows host at all (confirmed via `docker` CLI being entirely
unavailable in WSL). Resolved by starting Docker Desktop and restarting the lab
containers, which had stopped when Docker Desktop was last closed.

**Result:** `pip install -r requirements.txt` succeeded (all packages, including the
previously-unconfirmed `docker` SDK 7.1.0, installed cleanly). Discovery script executed
successfully against all 4 running lab services; output cross-checked field-by-field
against the Phase 1 ground truth table (privileged flag, network mode, host mount,
docker.sock mount, non-root user, cap_drop, read-only FS, resource limits, healthcheck,
restart policy) — full match, no discrepancies. `pytest tests/test_docker_discovery.py -v`
— 5/5 tests passed.

**Evidence:** evidence/logs/phase2/P02_files_created_confirmation.txt,
P02_pip_install_output.txt, P02_discovery_output.json, P02_pytest_output.txt — all
committed.

**Next step:** Phase 3 — Rule Engine (DOCKER-001 through DOCKER-015), using the now-
verified ServiceSnapshot as input.

**Thesis section affected:** Chapter 4, §4.3 (Implémentation du module de découverte) —
now fully writable with real evidence. Also feeds §5.2 methodology as the project's
first validated component.
