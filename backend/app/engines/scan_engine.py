
from urllib.parse import urlparse

from backend.app.ml.url_model import predict_url
from backend.app.engines.dns_engine import analyze_dns
from backend.app.engines.ssl_engine import analyze_ssl


def get_risk_level(score):
    if score >= 70:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def normalize_probability(value):
    if value is None:
        return None

    value = float(value)

    if value > 1:
        value /= 100

    return max(0.0, min(1.0, value))


def add_evidence(
    evidence,
    source,
    evidence_type,
    severity,
    title,
    description,
    value=None
):
    evidence.append({
        "source": source,
        "type": evidence_type,
        "severity": severity,
        "title": title,
        "description": description,
        "value": value
    })


def classify_dns_indicator(indicator):
    text = indicator.lower()

    if any(term in text for term in (
        "private ip",
        "loopback",
        "reserved ip",
        "non-public ip",
        "suspicious ip"
    )):
        return "high"

    if any(term in text for term in (
        "no ipv4",
        "no ipv6",
        "no address records",
        "not resolved"
    )):
        return "informational"

    return "medium"


def classify_ssl_indicator(indicator):
    text = indicator.lower()

    if any(term in text for term in (
        "hostname mismatch",
        "certificate has expired",
        "certificate is not yet valid",
        "certificate verification failed"
    )):
        return "high"

    if any(term in text for term in (
        "self-signed",
        "subject and issuer are identical"
    )):
        return "medium"

    return "informational"


def analyze_url_comprehensive(url: str):
    url = url.strip()

    if not url:
        raise ValueError("URL cannot be empty")

    parsed = urlparse(
        url if "://" in url else "https://" + url
    )

    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are supported")

    if not parsed.hostname:
        raise ValueError("Invalid URL: hostname is missing")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not supported")

    # --------------------------------------------------
    # 1. URL MACHINE LEARNING ANALYSIS
    # --------------------------------------------------

    ml_result = predict_url(url)

    probability = normalize_probability(
        ml_result.get("phishing_probability")
    )

    if probability is None:
        raise ValueError(
            "URL model did not return a phishing probability"
        )

    risk_score = round(probability * 100, 2)
    risk_level = get_risk_level(risk_score)

    # --------------------------------------------------
    # 2. DNS ANALYSIS
    # --------------------------------------------------

    try:
        dns_result = analyze_dns(url)
        dns_status = "completed"
        dns_error = None

    except Exception as error:
        dns_result = None
        dns_status = "unavailable"
        dns_error = str(error)

    # --------------------------------------------------
    # 3. SSL/TLS ANALYSIS
    # --------------------------------------------------

    if parsed.scheme.lower() != "https":
        ssl_result = None
        ssl_status = "not_applicable"
        ssl_error = None

    else:
        try:
            ssl_result = analyze_ssl(url)

            if ssl_result.get("status") in (
                "verified",
                "unverified"
            ):
                ssl_status = "completed"
            else:
                ssl_status = "unavailable"

            ssl_error = None

        except Exception as error:
            ssl_result = None
            ssl_status = "unavailable"
            ssl_error = str(error)

    # --------------------------------------------------
    # 4. EVIDENCE COLLECTION
    # --------------------------------------------------

    evidence = []

    # URL ML evidence
    if probability >= 0.70:
        ml_severity = "high"
    elif probability >= 0.30:
        ml_severity = "medium"
    else:
        ml_severity = "informational"

    add_evidence(
        evidence,
        source="URL ML model",
        evidence_type="model_prediction",
        severity=ml_severity,
        title=f"Model prediction: {ml_result.get('prediction', 'unknown')}",
        description=(
            f"The {ml_result.get('model', 'URL ML model')} assigned "
            f"a phishing probability of {probability * 100:.2f}% "
            f"using {ml_result.get('features_used', 'unknown')} URL features."
        ),
        value={
            "prediction": ml_result.get("prediction"),
            "phishing_probability": round(probability, 4),
            "risk_score": risk_score
        }
    )

    # DNS status evidence
    if dns_status == "completed":
        resolution_status = dns_result.get(
            "resolution_status",
            "unknown"
        )

        if resolution_status == "resolved":
            add_evidence(
                evidence,
                "DNS",
                "resolution_status",
                "informational",
                "Hostname resolved",
                "DNS returned address records for the hostname.",
                resolution_status
            )

        elif resolution_status == "not_resolved":
            add_evidence(
                evidence,
                "DNS",
                "resolution_status",
                "informational",
                "Hostname not resolved",
                (
                    "No usable IPv4 or IPv6 address records were found. "
                    "This may indicate an inactive hostname or a DNS issue; "
                    "it does not independently prove phishing."
                ),
                resolution_status
            )

        for indicator in dns_result.get(
            "security_indicators", []
        ):
            severity = classify_dns_indicator(indicator)

            add_evidence(
                evidence,
                "DNS",
                "security_indicator",
                severity,
                "DNS security observation",
                indicator,
                indicator
            )

        email_security = dns_result.get(
            "email_security",
            {}
        )

        if email_security.get("spf_present") is True:
            add_evidence(
                evidence,
                "DNS",
                "email_authentication",
                "informational",
                "SPF record present",
                (
                    "An SPF record was found for the registered domain. "
                    "This is an email authentication signal, not proof "
                    "of website legitimacy."
                ),
                True
            )

        elif email_security.get("spf_present") is False:
            add_evidence(
                evidence,
                "DNS",
                "email_authentication",
                "informational",
                "SPF record not found",
                (
                    "No SPF record was detected. This concerns email "
                    "authentication and is not independently evidence "
                    "of a malicious website."
                ),
                False
            )

        if email_security.get("dmarc_present") is True:
            add_evidence(
                evidence,
                "DNS",
                "email_authentication",
                "informational",
                "DMARC record present",
                (
                    "A DMARC record was found for the registered domain. "
                    "This is an email authentication signal."
                ),
                True
            )

        elif email_security.get("dmarc_present") is False:
            add_evidence(
                evidence,
                "DNS",
                "email_authentication",
                "informational",
                "DMARC record not found",
                (
                    "No DMARC record was detected. This is an email "
                    "authentication observation, not proof of phishing."
                ),
                False
            )

    else:
        add_evidence(
            evidence,
            "DNS",
            "engine_status",
            "informational",
            "DNS analysis unavailable",
            "DNS analysis could not be completed.",
            dns_error
        )

    # SSL status and certificate evidence
    if ssl_status == "not_applicable":
        add_evidence(
            evidence,
            "SSL/TLS",
            "engine_status",
            "informational",
            "HTTPS inspection not applicable",
            "The submitted URL uses HTTP rather than HTTPS.",
            ssl_status
        )

    elif ssl_status == "unavailable":
        add_evidence(
            evidence,
            "SSL/TLS",
            "engine_status",
            "informational",
            "SSL inspection unavailable",
            (
                "A TLS certificate could not be inspected. "
                "This may be caused by DNS, connection or server issues."
            ),
            ssl_error or (
                ssl_result.get("status")
                if ssl_result else None
            )
        )

    elif ssl_result:
        if ssl_result.get("certificate_trusted") is True:
            add_evidence(
                evidence,
                "SSL/TLS",
                "certificate_trust",
                "informational",
                "Certificate chain verified",
                "The TLS certificate passed the system trust checks.",
                True
            )

        elif ssl_result.get("certificate_trusted") is False:
            add_evidence(
                evidence,
                "SSL/TLS",
                "certificate_trust",
                "high",
                "Certificate verification failed",
                ssl_result.get(
                    "verification_error",
                    "Certificate trust could not be established."
                ),
                False
            )

        certificate = ssl_result.get("certificate") or {}

        if certificate.get("hostname_match") is False:
            add_evidence(
                evidence,
                "SSL/TLS",
                "hostname_mismatch",
                "high",
                "Certificate hostname mismatch",
                "The certificate does not match the requested hostname.",
                False
            )

        for indicator in ssl_result.get(
            "security_indicators", []
        ):
            severity = classify_ssl_indicator(indicator)

            add_evidence(
                evidence,
                "SSL/TLS",
                "security_indicator",
                severity,
                "Certificate security observation",
                indicator,
                indicator
            )

    # --------------------------------------------------
    # 5. RISK RECOMMENDATION
    # --------------------------------------------------

    if risk_level == "HIGH":
        recommendation = (
            "Avoid opening this URL or entering personal information. "
            "Verify the website through an official source."
        )

    elif risk_level == "MEDIUM":
        recommendation = (
            "Proceed cautiously. Verify the domain and inspect the "
            "available security evidence before sharing information."
        )

    else:
        recommendation = (
            "No high phishing probability was detected by the URL model. "
            "Still verify the website before sharing sensitive information."
        )

    # --------------------------------------------------
    # 6. MODEL EXPLANATION
    # --------------------------------------------------

    model_explanation = {
        "prediction": ml_result.get("prediction"),
        "phishing_probability": round(probability, 4),
        "features_used": ml_result.get("features_used"),
        "model": ml_result.get("model"),
        "explanation": (
            "The prediction is based on the URL features processed by "
            "the trained Random Forest model. Feature-level attribution "
            "has not yet been implemented; SHAP explanations will be "
            "added after validating the model explainer."
        )
    }

    # --------------------------------------------------
    # 7. FINAL REPORT
    # --------------------------------------------------

    return {
        "scan_type": "comprehensive_url_scan",
        "url": url,

        "overall_assessment": {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "model_prediction": ml_result.get("prediction"),
            "phishing_probability": round(probability, 4),
            "scoring_method": (
                "URL ML phishing probability multiplied by 100. "
                "DNS and SSL are supporting evidence and do not yet "
                "modify the numerical score."
            ),
            "recommendation": recommendation
        },

        "engine_status": {
            "url_ml": "completed",
            "dns": dns_status,
            "ssl_tls": ssl_status
        },

        "analysis": {
            "url_ml": {
                "status": "completed",
                "result": ml_result
            },
            "dns": {
                "status": dns_status,
                "result": dns_result,
                "error": dns_error
            },
            "ssl_tls": {
                "status": ssl_status,
                "result": ssl_result,
                "error": ssl_error
            }
        },

        "model_explanation": model_explanation,

        "evidence_summary": {
            "total": len(evidence),
            "high": sum(
                item["severity"] == "high" for item in evidence
            ),
            "medium": sum(
                item["severity"] == "medium" for item in evidence
            ),
            "informational": sum(
                item["severity"] == "informational"
                for item in evidence
            )
        },

        "evidence": evidence,

        "notice": (
            "Risk score currently comes from the URL ML model alone. "
            "DNS and SSL findings are supporting evidence. A low score "
            "or valid TLS certificate does not guarantee that a website "
            "is legitimate."
        )
    }
