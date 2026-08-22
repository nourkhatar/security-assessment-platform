# Architecture Overview

## Three-Layer Philosophy

**Layer 1 — Technical Security (deterministic).**
Discovery → Rule Engine → Structured Findings → Technical Score.
No AI involvement. Fully reproducible from the same container configuration.

**Layer 2 — Contextual Risk (deterministic).**
Service Context (criticality, exposure, data sensitivity, dependencies) is combined with
Layer 1 findings via a documented, fixed weighting model to produce a contextual risk value.
Two services with identical technical scores can have different contextual risk.
No AI involvement.

**Layer 3 — AI Correlation.**
Consumes Layer 1 + Layer 2 outputs, plus runtime observations (Prometheus) and controlled
security-test results, as structured input. Produces prioritization, correlation narrative,
and remediation recommendations — always referencing finding IDs as evidence. Cannot
override or invent the technical score or contextual risk value. Explicitly states when
evidence is insufficient for a claim.

## System Diagram

Frontend (Jinja2 + HTMX)
        |
   FastAPI Backend
        |
  -----------------------------------------------
  | Discovery | Assessment Engine | Context/Risk |
  | (Docker/  | (Rules -> Findings)| Engine       |
  |  k8s SDK) |                   |              |
  -----------------------------------------------
        |                |               |
        v                v               v
              SQLite (services, findings, scores,
              context, runtime snapshots, tests)
                        |
                AI Correlation Layer (Claude API)
                  reads DB, never writes scores
                        |
                Reporting Engine
          (Jinja2 -> HTML -> PDF, SHA-256, QR)

External infra (docker-compose):
  Docker Engine (lab targets) -> cAdvisor -> Prometheus -> Grafana
  Kind cluster (Kubernetes PoC, later phase)

## Technology Stack Decisions

- **Backend: FastAPI** — async, typed via Pydantic, auto-generates OpenAPI docs (useful
  thesis appendix material), natural fit for the Finding/Context schemas.
- **Frontend: Server-rendered Jinja2 + HTMX** (not a React SPA) — chosen under deadline
  constraints (16 days to feature freeze). A separate JS toolchain would consume time
  better spent on the rule engine, contextual risk model, and AI layer, for UI polish
  that carries little academic weight relative to the platform's analytical core.
- **Data layer: SQLite** — zero-ops, file-based, trivially portable as an evidence
  artifact. No architectural need for Postgres at this scale.
- **Kubernetes: Kind** (not Minikube/full cluster) — lightweight, scriptable, disposable;
  appropriate for a proof of concept demonstrating architectural extensibility, not a
  production-grade Kubernetes security platform (explicitly out of scope).
- **Environment: WSL2 (Kali Linux distro) + Docker Desktop WSL2 integration.** Chosen
  over a full Kali VM (VirtualBox/VMware) to avoid nested virtualization: a VM-based
  setup would add a second full virtualization layer on top of what Docker/Kind already
  require, increasing the risk of networking issues between containers (relevant to
  DOCKER-006 host networking testing and Prometheus/cAdvisor scraping) and to
  Docker-in-Docker operations needed by Kind. WSL2 provides a single lightweight
  virtualization layer shared with Docker Desktop's existing engine.

## Deterministic vs. AI Boundary (Key Methodological Principle)

The technical score (Layer 1) and contextual risk value (Layer 2) are computed by pure
functions over structured findings and context data, with fully documented weights and
methodology (see docs/technical-notes/). These are unit-tested and reproducible: running
the same assessment against the same container configuration yields the same score.

The AI layer (Layer 3) is strictly read-only with respect to these values. It receives
them as input, along with runtime and test data, and produces interpretive output
(prioritization, narrative, remediation) that is validated against a structured schema
before storage. Any AI output that attempts to assign a numeric score is discarded by
the API layer. This separation is the platform's core methodological claim and is
directly testable/defensible in the thesis.
