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
