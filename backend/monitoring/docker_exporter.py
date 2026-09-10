"""
Minimal Prometheus exporter for Docker container metrics, using the Docker SDK
directly (docker.from_env()) instead of cAdvisor/cgroup access. Built to work
around Docker Desktop's VM-based architecture, where cAdvisor cannot see
container-level cgroups from within a WSL2 distro.

Exposes: CPU %, memory usage/limit/percent, running state, uptime — per
container matching the "lab-" prefix. Runs as a standalone HTTP server.
"""
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

import docker

PORT = 9101


def compute_cpu_percent(stats: dict) -> float:
    try:
        cpu_delta = (stats["cpu_stats"]["cpu_usage"]["total_usage"]
                     - stats["precpu_stats"]["cpu_usage"]["total_usage"])
        system_delta = (stats["cpu_stats"]["system_cpu_usage"]
                         - stats["precpu_stats"]["system_cpu_usage"])
        online_cpus = stats["cpu_stats"].get("online_cpus", 1) or 1
        if system_delta > 0 and cpu_delta > 0:
            return (cpu_delta / system_delta) * online_cpus * 100.0
    except (KeyError, TypeError, ZeroDivisionError):
        pass
    return 0.0


def collect_metrics() -> str:
    client = docker.from_env()
    containers = client.containers.list(all=True, filters={"name": "lab-"})

    lines = [
        "# HELP docker_container_cpu_percent CPU usage percentage",
        "# TYPE docker_container_cpu_percent gauge",
        "# HELP docker_container_memory_usage_bytes Memory usage in bytes",
        "# TYPE docker_container_memory_usage_bytes gauge",
        "# HELP docker_container_memory_percent Memory usage as percent of limit",
        "# TYPE docker_container_memory_percent gauge",
        "# HELP docker_container_running Container running state (1=running, 0=not)",
        "# TYPE docker_container_running gauge",
        "# HELP docker_container_uptime_seconds Seconds since container start",
        "# TYPE docker_container_uptime_seconds gauge",
    ]

    for c in containers:
        name = c.name
        is_running = c.status == "running"
        lines.append(f'docker_container_running{{name="{name}"}} {1 if is_running else 0}')

        if not is_running:
            continue

        try:
            stats = c.stats(stream=False)
            cpu_pct = compute_cpu_percent(stats)
            mem_usage = stats.get("memory_stats", {}).get("usage", 0)
            mem_limit = stats.get("memory_stats", {}).get("limit", 1)
            mem_pct = (mem_usage / mem_limit * 100.0) if mem_limit else 0.0

            started_at = c.attrs["State"]["StartedAt"]
            started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            uptime = (datetime.now(timezone.utc) - started).total_seconds()

            lines.append(f'docker_container_cpu_percent{{name="{name}"}} {cpu_pct:.4f}')
            lines.append(f'docker_container_memory_usage_bytes{{name="{name}"}} {mem_usage}')
            lines.append(f'docker_container_memory_percent{{name="{name}"}} {mem_pct:.4f}')
            lines.append(f'docker_container_uptime_seconds{{name="{name}"}} {uptime:.0f}')
        except Exception as e:
            print(f"[docker_exporter] WARNING: failed to get stats for {name}: {e}")

    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            try:
                body = collect_metrics().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4")
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress noisy default request logging


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), MetricsHandler)
    print(f"Docker exporter listening on :{PORT}/metrics")
    server.serve_forever()
