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

## Entry 4 — 9 September 2026 — Phase 3: Rule Engine (completed and verified)

**Objective:** Implement the 15 Docker security rules (DOCKER-001..015) per the frozen
§3.7 severity table, producing structured Finding objects from ServiceSnapshot input.

**Implementation:**
- backend/assessment/findings/finding.py: Finding model, FindingStatus/Severity enums,
  frozen SEVERITY_WEIGHT table matching §3.7 exactly.
- backend/assessment/rules/docker/rules.py: 15 rule functions, each returning
  (status, evidence) via a registry decorator pattern.
- backend/assessment/engine/rule_engine.py: RuleEngine class evaluating the full
  catalog against a ServiceSnapshot.

**Problem 1:** Files were instructed across three separate message blocks but not
created until explicitly run and individually verified via ls -la after each block —
repeating the same pattern as Phase 2's false start. Verifying file size after each
block before proceeding prevented a repeat of that error this time.

**Problem 2:** Running rule_engine.py directly as a script failed with
ModuleNotFoundError: No module named 'backend', because top-level imports execute
before the script's own sys.path fix (inside __main__) takes effect. Resolved by
running as a module instead: `python3 -m backend.assessment.engine.rule_engine`.
This will be the standard invocation method going forward for all manual script runs.

**Result:** All 15 rules executed successfully against all 4 lab services (60 verdicts
total). Cross-checked against Phase 1 ground truth — full match on all rules for
vuln-privileged, vuln-docker-socket, and vuln-web. hardened-api matched on 13/15,
with 2 verdicts surfacing genuine, documented findings rather than bugs:
(1) DOCKER-008 flags any exposed port without distinguishing necessary vs excessive
exposure — a known limitation of the rule's simplicity; (2) DOCKER-011 flags the
locally-built, untagged hardened-api image as unpinned — expected behavior for a
lab-built image without a registry tag; (3) DOCKER-015 produces a false positive on
the GPG_KEY environment variable inherited from the official python:3.12-slim base
image (a public key fingerprint, not a secret), due to naive substring keyword
matching. All three are documented rather than hidden.
pytest tests/test_rule_engine.py -v — 4/4 tests passed, encoding the actual verified
behavior including the above quirks.

**Evidence:** evidence/logs/phase3/P03_rule_engine_output.txt, P03_pytest_output.txt —
committed.

**Next step:** Phase 4 — Technical Scoring, implementing the frozen §3.7 formula
against these real Finding objects.

**Thesis section affected:** Chapter 4, §4.4 (Implémentation du moteur de règles).
Also feeds §5.2 (Résultats de l'évaluation technique) and §5.8 (Limites) with the
two documented quirks above as legitimate validation findings.

## Entry 5 — 9 September 2026 — Phase 4: Technical Scoring (completed and verified)

**Objective:** Implement the frozen §3.7 formula against real Finding objects from
Phase 3.

**Implementation:**
- backend/scoring/technical_score.py: calculate_technical_score(), pure function
  over a list of Finding objects. Excludes N/A findings from both numerator and
  denominator. Returns a TechnicalScore object with rounded and unrounded values.

**Result:** Scores computed for all 4 lab services and independently verified against
a manual hand-calculation performed before running the code:
lab-vuln-privileged=34, lab-vuln-docker-socket=58, lab-hardened-api=83, lab-vuln-web=54.
All four matched exactly. pytest suite (6 tests: 4 exact-score checks, reproducibility
across repeated runs, 0-100 range validity) — 6/6 passed.

**Evidence:** evidence/logs/phase4/P04_technical_scores.txt, P04_pytest_output.txt —
committed.

**Next step:** Phase 5+6 — Service Context model and Contextual Risk, implementing
the frozen §3.8 model. This phase produces the project's central experimental result:
demonstrating that identical technical scores yield different contextual risk under
different service context.

**Thesis section affected:** Chapter 4, §4.5 (Implémentation du scoring technique).
Feeds §5.2 as a headline result (score table alongside the rule-level findings from
Phase 3).

## Entry 6 — 9 September 2026 — Phase 5+6: Service Context & Contextual Risk (completed and verified)

**Objective:** Implement the frozen §3.8 contextual risk model and execute the
project's central experiment: identical technical score, different service context,
different contextual risk.

**Implementation:**
- backend/models/context.py: ServiceContext model, Criticality/Exposure/
  DataSensitivity enums, frozen point tables per §3.8.
- backend/context/contextual_risk.py: calculate_contextual_risk(), implementing
  Context Weight -> Context Tier, Technical Score -> Technical Tier, rank_sum ->
  Contextual Risk Level, exactly per the frozen tier boundaries.
- backend/context/run_experiment.py: the actual A/B experiment script, applying
  two ServiceContext profiles to the real, previously-verified technical score of
  lab-hardened-api (83).

**Result:** Real technical score (82.76, rounds to 83) held constant; Scenario A
(internal, low criticality, no sensitive data) produced Contextual Risk = LOW;
Scenario B (internet-facing, critical, PII) produced Contextual Risk = HIGH from
the identical technical score. This is the project's core methodological claim,
demonstrated with executed code against a real service rather than a hypothetical
example. pytest suite (6 tests: context weight boundaries, technical tier
boundaries, and the A/B experiment as an assertion) - 6/6 passed.

**Evidence:** evidence/logs/phase5-6/P056_context_experiment.txt,
P056_pytest_output.txt — committed.

**Next step:** reassess remaining scope given calendar position (9 September,
feature freeze target 7 September has technically passed per the original schedule,
though the project's internal phase sequencing is still mid-stream). Candidates:
Phase 7 (Monitoring), Phase 8 (AI), Phase 9 (Kubernetes PoC), Phase 10 (Security
Testing), Phase 11 (Reporting/QR) remain, per the original brief's own priority
classification, with AI and Kubernetes as the first reduction candidates if time
runs short.

**Thesis section affected:** Chapter 4, §4.6 (Contexte et calcul du risque
contextuel). This is the headline result for Chapter 5, §5.3 (Résultats de
l'évaluation contextuelle) — the core technical-score-vs-contextual-risk
comparison the entire project is built around.
