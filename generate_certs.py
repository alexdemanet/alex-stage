#!/usr/bin/env python3
"""Utility to create a simple CA and a server certificate for local testing.

Usage:
    python generate_certs.py [--force]

# The generated server certificate by default will include both the DNS name
# "localhost" and the IP address 127.0.0.1 in its SubjectAltName.  This makes
# it valid when clients connect using either host name or loopback IP.

Generates the following files under ./certs (directory created if missing):

    ca.key      CA private key (PEM)
    ca.crt      CA certificate (PEM, self-signed)
    server.key  Server private key (PEM)
    server.crt  Server certificate signed by CA (PEM)

The certificates use a 2048‑bit RSA key and SHA256 signatures.  The server
certificate includes "localhost" as a subjectAltName which is sufficient when
connecting to 127.0.0.1.

This is intended for development/test environments only.  Do *not* use for
production.
"""

import argparse
import datetime
import os
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

CERT_DIR = Path("certs")


def _mkdir():
    CERT_DIR.mkdir(exist_ok=True)


def _write_bytes(path: Path, data: bytes, mode: int = 0o644) -> None:
    with open(path, "wb") as f:
        f.write(data)
    os.chmod(path, mode)


def create_ca(force: bool = False):
    ca_key_path = CERT_DIR / "ca.key"
    ca_cert_path = CERT_DIR / "ca.crt"
    if not force and ca_key_path.exists() and ca_cert_path.exists():
        print(f"CA key/cert already exist ({ca_key_path},{ca_cert_path}), skip")
        return None, None

    print("Generating CA private key...")
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BE"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CLiegeA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Liege"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "hepl"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Example Local CA"),
    ])

    print("Creating CA certificate (self-signed)...")
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )

    _write_bytes(
        ca_key_path,
        ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        mode=0o600,
    )
    _write_bytes(ca_cert_path, ca_cert.public_bytes(serialization.Encoding.PEM))

    print(f"Wrote CA key to {ca_key_path}")
    print(f"Wrote CA cert to {ca_cert_path}")
    return ca_key, ca_cert


def create_server_cert(ca_key, ca_cert, force: bool = False):
    srv_key_path = CERT_DIR / "server.key"
    srv_cert_path = CERT_DIR / "server.crt"
    if not force and srv_key_path.exists() and srv_cert_path.exists():
        print(f"Server key/cert already exist ({srv_key_path},{srv_cert_path}), skip")
        return

    print("Generating server private key...")
    srv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Localhost"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Example Server"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    # include both DNS and IP SANs so cert works for localhost and 127.0.0.1
    from ipaddress import IPv4Address

    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(subject)
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(srv_key, hashes.SHA256())
    )

    print("Signing server certificate with CA...")
    srv_cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(ca_cert.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=825))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            # include the same SANs as in the CSR (DNS + IP address)
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    _write_bytes(
        srv_key_path,
        srv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        mode=0o600,
    )
    _write_bytes(srv_cert_path, srv_cert.public_bytes(serialization.Encoding.PEM))

    print(f"Wrote server key to {srv_key_path}")
    print(f"Wrote server cert to {srv_cert_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate CA and server certs")
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing files",
    )
    args = parser.parse_args()

    _mkdir()
    ca_key, ca_cert = create_ca(args.force)
    if ca_key is None:
        # reload existing CA cert/key for signing
        from cryptography.hazmat.primitives import serialization as _ser
        with open(CERT_DIR / "ca.key", "rb") as f:
            ca_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(CERT_DIR / "ca.crt", "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())
    create_server_cert(ca_key, ca_cert, args.force)


if __name__ == "__main__":
    main()
