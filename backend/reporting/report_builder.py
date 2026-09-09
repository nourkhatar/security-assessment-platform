"""
Report generation: assembles Discovery + Rule Engine + Technical Score +
Contextual Risk output into an HTML report, renders to PDF via WeasyPrint,
and computes a SHA-256 integrity hash of the resulting PDF.
"""
import os
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from backend.discovery.docker.docker_discovery import DockerDiscovery
from backend.assessment.engine.rule_engine import RuleEngine
from backend.scoring.technical_score import calculate_technical_score
from backend.assessment.findings.finding import FindingStatus
from backend.integrity.hashing import compute_sha256

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def build_report(output_path: str, context_by_service: dict = None):
    context_by_service = context_by_service or {}

    discovery = DockerDiscovery()
    services = discovery.discover_all()
    engine = RuleEngine(run_id=f"report-{datetime.now(timezone.utc).isoformat()}")

    service_data = []
    for s in services:
        findings = engine.evaluate(s)
        ts = calculate_technical_score(findings)

        contextual_risk = None
        if s.name in context_by_service:
            from backend.context.contextual_risk import calculate_contextual_risk
            risk = calculate_contextual_risk(ts.score, context_by_service[s.name])
            contextual_risk = risk.contextual_risk_level.value

        findings_data = []
        for f in findings:
            findings_data.append({
                "rule_id": f.rule_id,
                "rule_name": f.rule_name,
                "severity": f.severity.value,
                "status": f.status.value,
                "status_class": f.status.value.replace("/", ""),
                "evidence_summary": str(f.evidence),
            })

        service_data.append({
            "name": s.name,
            "technical_score": ts.score_rounded,
            "contextual_risk": contextual_risk,
            "findings": findings_data,
        })

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report.html")
    html_content = template.render(
        run_id=engine.run_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        services=service_data,
    )

    html_path = output_path.replace(".pdf", ".html")
    with open(html_path, "w") as f:
        f.write(html_content)

    HTML(string=html_content).write_pdf(output_path)

    report_hash = compute_sha256(output_path)
    hash_path = output_path + ".sha256"
    with open(hash_path, "w") as f:
        f.write(report_hash)

    return output_path, report_hash


if __name__ == "__main__":
    from backend.models.context import ServiceContext, Criticality, Exposure, DataSensitivity

    contexts = {
        "lab-vuln-web": ServiceContext(service="lab-vuln-web", criticality=Criticality.LOW,
                                        exposure=Exposure.INTERNAL_ONLY, data_sensitivity=DataSensitivity.NONE),
        "lab-vuln-privileged": ServiceContext(service="lab-vuln-privileged", criticality=Criticality.MEDIUM,
                                               exposure=Exposure.INTERNAL_NETWORK, data_sensitivity=DataSensitivity.INTERNAL),
        "lab-vuln-docker-socket": ServiceContext(service="lab-vuln-docker-socket", criticality=Criticality.HIGH,
                                                  exposure=Exposure.INTERNAL_NETWORK, data_sensitivity=DataSensitivity.INTERNAL),
        "lab-hardened-api": ServiceContext(service="lab-hardened-api", criticality=Criticality.LOW,
                                            exposure=Exposure.INTERNAL_ONLY, data_sensitivity=DataSensitivity.NONE),
    }

    path, h = build_report("evidence/reports/assessment_report.pdf", contexts)
    print(f"Report generated: {path}")
    print(f"SHA-256: {h}")
