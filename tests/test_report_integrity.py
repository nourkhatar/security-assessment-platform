import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.integrity.hashing import compute_sha256, verify_sha256


def test_hash_is_deterministic(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("assessment report content")
    h1 = compute_sha256(str(f))
    h2 = compute_sha256(str(f))
    assert h1 == h2


def test_verify_detects_unmodified_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("assessment report content")
    h = compute_sha256(str(f))
    assert verify_sha256(str(f), h) is True


def test_verify_detects_tampering(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("original content")
    h = compute_sha256(str(f))

    # Simulate tampering after the hash was recorded
    f.write_text("tampered content")

    assert verify_sha256(str(f), h) is False


def test_real_report_hash_matches_saved_hash():
    report_path = "evidence/reports/assessment_report.pdf"
    hash_path = report_path + ".sha256"
    with open(hash_path) as f:
        saved_hash = f.read().strip()
    assert verify_sha256(report_path, saved_hash) is True
