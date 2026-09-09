"""
Report integrity — SHA-256 hashing of the generated report file.
"""
import hashlib


def compute_sha256(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_sha256(filepath: str, expected_hash: str) -> bool:
    return compute_sha256(filepath) == expected_hash
