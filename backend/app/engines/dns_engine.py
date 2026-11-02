
import ipaddress
from urllib.parse import urlparse

import dns.exception
import dns.resolver
import tldextract


DNS_TIMEOUT = 1.5
DNS_LIFETIME = 2.0

extract_domain = tldextract.TLDExtract(
    suffix_list_urls=(),
    include_psl_private_domains=True
)


def extract_hostname(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A valid URL is required")

    value = url.strip()

    if "://" not in value:
        value = "https://" + value

    parsed = urlparse(value)
    hostname = parsed.hostname

    if not hostname:
        raise ValueError("Could not extract hostname from URL")

    try:
        return hostname.encode("idna").decode("ascii").lower()
    except UnicodeError:
        raise ValueError("Invalid internationalized domain name")


def get_registered_domain(hostname: str):
    try:
        ipaddress.ip_address(hostname)
        return None
    except ValueError:
        pass

    extracted = extract_domain(hostname)
    return extracted.top_domain_under_public_suffix or None


def create_resolver():
    resolver = dns.resolver.Resolver(configure=True)
    resolver.timeout = DNS_TIMEOUT
    resolver.lifetime = DNS_LIFETIME
    return resolver


def query_record(resolver, hostname: str, record_type: str):
    try:
        answer = resolver.resolve(
            hostname,
            record_type,
            search=False,
            lifetime=DNS_LIFETIME
        )

        if record_type == "TXT":
            records = [
                b"".join(record.strings).decode("utf-8", errors="replace")
                for record in answer
            ]
        else:
            records = [record.to_text() for record in answer]

        ttl = answer.rrset.ttl if answer.rrset else None

        return {
            "status": "found",
            "records": records,
            "count": len(records),
            "ttl": ttl
        }

    except dns.resolver.NXDOMAIN:
        return {
            "status": "nxdomain",
            "records": [],
            "count": 0,
            "ttl": None
        }

    except dns.resolver.NoAnswer:
        return {
            "status": "no_answer",
            "records": [],
            "count": 0,
            "ttl": None
        }

    except dns.resolver.NoNameservers:
        return {
            "status": "no_nameservers",
            "records": [],
            "count": 0,
            "ttl": None
        }

    except dns.exception.Timeout:
        return {
            "status": "timeout",
            "records": [],
            "count": 0,
            "ttl": None
        }

    except dns.exception.DNSException:
        return {
            "status": "error",
            "records": [],
            "count": 0,
            "ttl": None
        }


def inspect_ip_addresses(records):
    results = []

    for value in records:
        try:
            address = ipaddress.ip_address(value)

            results.append({
                "ip": value,
                "version": address.version,
                "is_private": address.is_private,
                "is_global": address.is_global,
                "is_reserved": address.is_reserved,
                "is_loopback": address.is_loopback
            })

        except ValueError:
            continue

    return results


def analyze_dns(url: str):
    hostname = extract_hostname(url)
    registered_domain = get_registered_domain(hostname)

    try:
        ipaddress.ip_address(hostname)

        return {
            "hostname": hostname,
            "registered_domain": None,
            "resolution_status": "ip_address",
            "message": "The submitted URL uses an IP address directly.",
            "records": {},
            "ip_analysis": inspect_ip_addresses([hostname]),
            "security_indicators": [
                "URL uses a direct IP address instead of a domain name"
            ]
        }

    except ValueError:
        pass

    if not registered_domain:
        raise ValueError("Could not determine registered domain")

    resolver = create_resolver()

    records = {
        "A": query_record(resolver, hostname, "A"),
        "AAAA": query_record(resolver, hostname, "AAAA"),
        "CNAME": query_record(resolver, hostname, "CNAME"),
        "NS": query_record(resolver, registered_domain, "NS"),
        "MX": query_record(resolver, registered_domain, "MX"),
        "TXT": query_record(resolver, registered_domain, "TXT"),
        "DMARC": query_record(
            resolver,
            f"_dmarc.{registered_domain}",
            "TXT"
        )
    }

    ip_values = (
        records["A"]["records"] +
        records["AAAA"]["records"]
    )

    ip_analysis = inspect_ip_addresses(ip_values)

    # SPF and DMARC detection
    txt_records = records["TXT"]["records"]
    dmarc_records = records["DMARC"]["records"]

    has_spf = (
        any(
            value.strip().lower().startswith("v=spf1")
            for value in txt_records
        )
        if records["TXT"]["status"] == "found"
        else None
    )

    has_dmarc = (
        any(
            value.strip().lower().startswith("v=dmarc1")
            for value in dmarc_records
        )
        if records["DMARC"]["status"] == "found"
        else None
    )

    # Security indicators
    indicators = []

    if records["A"]["status"] == "nxdomain":
        indicators.append("Hostname does not exist in DNS")

    if not records["A"]["count"] and not records["AAAA"]["count"]:
        indicators.append("No IPv4 or IPv6 address records found")

    if any(not item["is_global"] for item in ip_analysis):
        indicators.append(
            "DNS returned a private, reserved or non-global IP address"
        )

    if has_spf is False:
        indicators.append(
            "No SPF record detected at the registered domain"
        )
    elif has_spf is None:
        indicators.append("SPF status could not be determined")

    if has_dmarc is False:
        indicators.append("No DMARC record detected")
    elif has_dmarc is None:
        indicators.append("DMARC status could not be determined")

    # TTL summary
    ttl_values = [
        result["ttl"]
        for result in records.values()
        if result["ttl"] is not None
    ]

    resolution_status = (
        "resolved"
        if records["A"]["count"] or records["AAAA"]["count"]
        else "not_resolved"
    )

    return {
        "hostname": hostname,
        "registered_domain": registered_domain,
        "resolution_status": resolution_status,
        "records": records,
        "ip_analysis": ip_analysis,
        "email_security": {
            "spf_present": has_spf,
            "dmarc_present": has_dmarc
        },
        "ttl_summary": {
            "minimum": min(ttl_values) if ttl_values else None,
            "maximum": max(ttl_values) if ttl_values else None
        },
        "security_indicators": indicators,
        "notice": (
            "DNS indicators provide supporting evidence only. "
            "They do not independently determine whether a URL is malicious."
        )
    }
