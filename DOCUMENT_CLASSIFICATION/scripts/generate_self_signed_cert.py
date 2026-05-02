import argparse
import datetime
from ipaddress import ip_address
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def _parse_sans(value: str):
    if not value:
        return []
    items = [v.strip() for v in value.split(',') if v.strip()]
    sans = []
    for item in items:
        try:
            sans.append(x509.IPAddress(ip_address(item)))
        except ValueError:
            sans.append(x509.DNSName(item))
    return sans


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate a self-signed SSL cert')
    parser.add_argument('--cert', default='certs/localhost.pem', help='Path to cert file')
    parser.add_argument('--key', default='certs/localhost.key', help='Path to key file')
    parser.add_argument('--days', type=int, default=365, help='Validity in days')
    parser.add_argument('--cn', default='localhost', help='Common Name')
    parser.add_argument('--san', default='localhost,127.0.0.1,::1', help='Comma-separated SANs')
    args = parser.parse_args()

    cert_path = Path(args.cert)
    key_path = Path(args.key)
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, 'IN'),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'NA'),
        x509.NameAttribute(NameOID.LOCALITY_NAME, 'NA'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'SmartDoc AI'),
        x509.NameAttribute(NameOID.COMMON_NAME, args.cn),
    ])

    now = datetime.datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=args.days))
        .add_extension(
            x509.SubjectAlternativeName(_parse_sans(args.san)),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    key_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    cert_bytes = cert.public_bytes(serialization.Encoding.PEM)

    key_path.write_bytes(key_bytes)
    cert_path.write_bytes(cert_bytes)

    print(f'Generated key: {key_path}')
    print(f'Generated cert: {cert_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
