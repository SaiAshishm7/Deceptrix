
import ipaddress
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

import dns.exception
import dns.resolver

from cryptography import x509
from cryptography.hazmat.primitives import hashes


DNS_TIMEOUT = 2.0
TLS_TIMEOUT = 4.0
MAX_ADDRESSES = 64


def extract_https_target(url: str):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A valid URL is required")

    value = url.strip()

    if any(ord(char) < 32 for char in value):
        raise ValueError("URL contains invalid control characters")

    if "://" not in value:
        value = "https://" + value

    parsed = urlparse(value)

    if parsed.scheme.lower() != "https":
        raise ValueError("SSL inspection requires an HTTPS URL")

    if not parsed.hostname:
        raise ValueError("Could not extract hostname")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not supported")

    try:
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
    except UnicodeError:
        raise ValueError("Invalid hostname")

    try:
        port = parsed.port or 443
    except ValueError:
        raise ValueError("Invalid port")

    if port != 443:
        raise ValueError("Only HTTPS port 443 is supported")

    return hostname, port


def validate_public_ip(value: str):
    address = ipaddress.ip_address(value)

    if not address.is_global:
        raise ValueError(
            f"Inspection blocked: {value} is not a globally routable IP"
        )

    return address


def resolve_public_addresses(hostname: str):
    try:
        literal_ip = ipaddress.ip_address(hostname)
        validate_public_ip(str(literal_ip))
        return [str(literal_ip)]

    except ValueError as error:
        if "not a globally routable IP" in str(error):
            raise
        if "%" in hostname:
            raise ValueError("Scoped IP addresses are not supported")

    resolver = dns.resolver.Resolver(configure=True)
    resolver.timeout = DNS_TIMEOUT
    resolver.lifetime = DNS_TIMEOUT

    addresses = []

    for record_type in ("A", "AAAA"):
        try:
            answers = resolver.resolve(
                hostname,
                record_type,
                search=False,
                lifetime=DNS_TIMEOUT
            )

            for answer in answers:
                address = validate_public_ip(answer.to_text())
                addresses.append(str(address))

        except dns.resolver.NXDOMAIN:
            continue
        except dns.resolver.NoAnswer:
            continue
        except dns.resolver.NoNameservers:
            continue
        except dns.exception.Timeout as error:
            raise ValueError(
                f"DNS resolution timed out for {record_type}; "
                "TLS inspection aborted"
            ) from error

    addresses = list(dict.fromkeys(addresses))

    if not addresses:
        raise ValueError("Hostname did not resolve to a public IP address")

    if len(addresses) > MAX_ADDRESSES:
        raise ValueError("Too many resolved IP addresses")

    return addresses


def connect_to_pinned_ip(ip: str, port: int, hostname: str, verify: bool):
    address = ipaddress.ip_address(ip)

    if not address.is_global:
        raise ValueError("Non-public IP connection blocked")

    context = ssl.create_default_context()

    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    raw_socket = socket.socket(
        socket.AF_INET6 if address.version == 6 else socket.AF_INET,
        socket.SOCK_STREAM
    )

    raw_socket.settimeout(TLS_TIMEOUT)

    try:
        if address.version == 6:
            raw_socket.connect((str(address), port, 0, 0))
        else:
            raw_socket.connect((str(address), port))

        return context.wrap_socket(
            raw_socket,
            server_hostname=hostname
        )

    except Exception:
        raw_socket.close()
        raise


def certificate_name_data(certificate):
    subject = tuple(
        tuple((attribute.oid._name, attribute.value) for attribute in group)
        for group in certificate.subject.rdns
    )

    issuer = tuple(
        tuple((attribute.oid._name, attribute.value) for attribute in group)
        for group in certificate.issuer.rdns
    )

    san_values = []

    try:
        extension = certificate.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )

        for name in extension.value:
            if isinstance(name, x509.DNSName):
                san_values.append(("DNS", name.value))
            elif isinstance(name, x509.IPAddress):
                san_values.append(("IP Address", str(name.value)))

    except x509.ExtensionNotFound:
        pass

    return subject, issuer, san_values



def certificate_hostname_matches(certificate, hostname):
    import ipaddress

    try:
        requested_ip = ipaddress.ip_address(hostname)
    except ValueError:
        requested_ip = None

    try:
        san = certificate.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value
    except x509.ExtensionNotFound:
        return False

    if requested_ip is not None:
        certificate_ips = san.get_values_for_type(x509.IPAddress)
        return any(
            requested_ip == certificate_ip
            for certificate_ip in certificate_ips
        )

    dns_names = san.get_values_for_type(x509.DNSName)
    hostname = hostname.rstrip(".").lower()

    for certificate_name in dns_names:
        certificate_name = certificate_name.rstrip(".").lower()

        if certificate_name == hostname:
            return True

        if certificate_name.startswith("*."):
            suffix = certificate_name[2:]

            if (
                hostname.endswith("." + suffix)
                and hostname.count(".") == suffix.count(".") + 1
            ):
                return True

    return False


def inspect_certificate(der_certificate: bytes, hostname: str):
    certificate = x509.load_der_x509_certificate(der_certificate)

    san_values = []

    try:
        extension = certificate.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )

        for name in extension.value:
            if isinstance(name, x509.DNSName):
                san_values.append(("DNS", name.value))
            elif isinstance(name, x509.IPAddress):
                san_values.append(("IP Address", str(name.value)))

    except x509.ExtensionNotFound:
        pass

    now = datetime.now(timezone.utc)

    not_before = certificate.not_valid_before_utc
    not_after = certificate.not_valid_after_utc

    is_expired = now > not_after
    is_not_yet_valid = now < not_before

    hostname_match = certificate_hostname_matches(
        certificate, hostname
    )

    self_signed_indicator = (
        certificate.subject == certificate.issuer
    )

    fingerprint = certificate.fingerprint(
        hashes.SHA256()
    ).hex(":")

    return {
        "subject": certificate.subject.rfc4514_string(),
        "issuer": certificate.issuer.rfc4514_string(),
        "valid_from": not_before.isoformat(),
        "valid_until": not_after.isoformat(),
        "is_expired": is_expired,
        "is_not_yet_valid": is_not_yet_valid,
        "hostname_match": hostname_match,
        "subject_alternative_names": san_values,
        "self_signed_indicator": self_signed_indicator,
        "sha256_fingerprint": fingerprint,
        "serial_number": str(certificate.serial_number)
    }



def inspect_tls_version(sock):
    return sock.version()


def analyze_ssl(url: str):
    hostname, port = extract_https_target(url)

    addresses = resolve_public_addresses(hostname)

    verified_socket = None
    certificate_data = None
    tls_version = None
    verification_error = None
    successful_ip = None

    for ip in addresses:
        try:
            verified_socket = connect_to_pinned_ip(
                ip, port, hostname, verify=True
            )

            der = verified_socket.getpeercert(binary_form=True)
            certificate_data = inspect_certificate(der, hostname)
            tls_version = inspect_tls_version(verified_socket)
            successful_ip = ip
            verified_socket.close()
            break

        except (ssl.SSLError, OSError, ValueError) as error:
            verification_error = str(error)

            if verified_socket:
                try:
                    verified_socket.close()
                except OSError:
                    pass

            verified_socket = None

    if certificate_data is None:
        for ip in addresses:
            diagnostic_socket = None

            try:
                diagnostic_socket = connect_to_pinned_ip(
                    ip, port, hostname, verify=False
                )

                der = diagnostic_socket.getpeercert(binary_form=True)
                certificate_data = inspect_certificate(der, hostname)
                tls_version = inspect_tls_version(diagnostic_socket)
                successful_ip = ip
                diagnostic_socket.close()
                break

            except (ssl.SSLError, OSError, ValueError):
                if diagnostic_socket:
                    try:
                        diagnostic_socket.close()
                    except OSError:
                        pass

    if certificate_data is None:
        return {
            "hostname": hostname,
            "status": "unavailable",
            "certificate": None,
            "tls_version": None,
            "connection_ip": None,
            "verification_error": verification_error,
            "security_indicators": [
                "Could not establish a TLS connection or retrieve a certificate"
            ]
        }

    indicators = []

    if verification_error:
        indicators.append(
            "Certificate verification failed: " + verification_error
        )

    if certificate_data["is_expired"]:
        indicators.append("Certificate has expired")

    if certificate_data["is_not_yet_valid"]:
        indicators.append("Certificate is not yet valid")

    if not certificate_data["hostname_match"]:
        indicators.append("Certificate hostname mismatch")

    if certificate_data["self_signed_indicator"]:
        indicators.append("Certificate subject and issuer are identical")

    trusted = verification_error is None

    return {
        "hostname": hostname,
        "status": "verified" if trusted else "unverified",
        "certificate_trusted": trusted,
        "tls_version": tls_version,
        "connection_ip": successful_ip,
        "certificate": certificate_data,
        "verification_error": verification_error,
        "security_indicators": indicators,
        "notice": (
            "A valid TLS certificate protects the connection but does not "
            "prove that the website itself is legitimate."
        )
    }
