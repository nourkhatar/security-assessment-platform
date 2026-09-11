"""
QR verification artifact generation.

The QR code encodes the SHA-256 fingerprint of a generated report.
It provides a convenient way to retrieve/compare the report fingerprint;
it does not constitute a digital signature or proof of authenticity.
"""
import qrcode


def generate_hash_qr(report_hash: str, output_path: str) -> str:
    payload = f"SHA256:{report_hash}"

    image = qrcode.make(payload)
    image.save(output_path)

    return output_path
