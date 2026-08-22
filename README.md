# Intelligent Security Assessment and Contextual Risk Monitoring Platform for Containerized Environments

Cybersecurity engineering thesis project (4th year) — a platform that evaluates the
security posture of containerized services (Docker, with a Kubernetes proof of concept),
combining three distinct analytical layers:

1. **Technical Security** — deterministic, rule-based assessment of Docker configurations
   (root execution, privileged mode, capabilities, mounts, networking, etc.), producing a
   reproducible technical score.
2. **Contextual Risk** — a deterministic model that adjusts raw technical findings against
   real-world service context (criticality, exposure, data sensitivity, dependencies),
   because identical technical scores do not represent identical real-world risk.
3. **AI Correlation** — an LLM (Claude) that interprets, correlates, and prioritizes findings,
   context, runtime observations, and controlled test results, and drafts remediation
   recommendations — always referencing the underlying deterministic evidence, and explicitly
   flagging when evidence is insufficient. The AI layer never determines the technical score
   or the contextual risk value.

The platform also collects container runtime metrics via Prometheus/Grafana, runs a small
set of controlled security tests in an isolated lab, and produces an automated report with
a SHA-256 integrity hash and QR verification code.

## Status
Phase 0 — Architecture & environment setup. See `docs/technical-journal.md` for progress log.

## Environment
- WSL2 (Kali Linux) on Windows 11
- Docker Engine 29.3.1 + Docker Compose v5.1.1
- Python 3.13, FastAPI backend
- kubectl v1.34.1, Kind v0.27.0 (Kubernetes PoC)
- Prometheus + Grafana (containerized)
- Claude API for the AI correlation layer

## Structure
See `docs/architecture/architecture-overview.md` for the full architecture and rationale.
