
import math
import re
import ipaddress
from collections import Counter
from urllib.parse import urlparse, parse_qs


HIGH_RISK_EXTENSIONS = (
    ".exe", ".msi", ".bat", ".cmd", ".vbs", ".ps1",
    ".jar", ".scr", ".app", ".dmg", ".pkg", ".sh",
    ".run", ".bin", ".py", ".air", ".apk", ".elf",
    ".zip", ".rar", ".7z"
)


def calculate_entropy(value):
    if not value:
        return 0.0

    counts = Counter(value)
    length = len(value)

    return -sum(
        (count / length) * math.log2(count / length)
        for count in counts.values()
    )


def is_ip_address(hostname):
    try:
        ipaddress.ip_address(hostname)
        return 1
    except ValueError:
        return 0


def extract_url_features(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A valid URL is required.")

    url = url.strip()

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    domain_for_length = re.sub(
        r"^www\.",
        "",
        parsed.netloc,
        flags=re.IGNORECASE
    )
    path = parsed.path or ""
    query = parsed.query or ""

    if not parsed.scheme or not hostname:
        raise ValueError("URL must include a valid scheme and hostname.")

    words = re.split(r"\W+", url)
    word_lengths = [len(word) for word in words]

    digits = sum(char.isdigit() for char in url)
    hostname_digits = sum(char.isdigit() for char in hostname)

    special_characters = (
        "@,$,%20,&,=,%,? ,_,-,;"
    )

    features = {
        "dots_path": path.count("."),
        "url_length": len(url),
        "domain_length": len(domain_for_length),
        "url_contains_ip": is_ip_address(hostname),
        "special_characters_count": sum(
            url.count(char) for char in
            ["@", ",", "$", "&", "=", "%", "?", "_", "-", ";"]
        ) + url.count("%20"),
        "no_of_at": url.count("@"),
        "no_of_comma": url.count(","),
        "no_of_dollar": url.count("$"),
        "no_of_semicolon": url.count(";"),
        "no_of_space": url.count(" "),
        "no_of_ampersand": url.count("&"),
        "no_of_dots": url.count("."),
        "no_of_equal": url.count("="),
        "no_of_percent": url.count("%"),
        "no_of_underscore": url.count("_"),
        "no_of_hyphen": url.count("-"),
        "no_of_questionmark": url.count("?"),
        "no_of_colon": url.count(":"),
        "no_of_slashes_inpath": path.count("/"),
        "has_asterisk": int("*" in url),
        "has_or": int("|" in url),
        "has_embedded_url": int(
            len(re.findall(r"https?://", url, re.IGNORECASE)) > 1
        ),
        "uses_https": int(parsed.scheme.lower() == "https"),
        "num_query_params": len(parse_qs(query)),
        "numeric_proportion": digits / len(url) if url else 0.0,
        "url_entropy": calculate_entropy(url),
        "hostname_digit_ratio": (
            hostname_digits / len(hostname) if hostname else 0.0
        ),
        "has_redirections": int(
            "//" in url[len(parsed.scheme) + 3:]
        ),
        "has_punycode": int("xn--" in hostname.lower()),
        "count_www": url.lower().count("www"),
        "count_com": url.lower().count("com"),
        "url_has_high_risk_extension": int(
            any(ext in url.lower() for ext in HIGH_RISK_EXTENSIONS)
        ),
        "has_explicit_port": int(parsed.port is not None),
        "total_words_url": len(words),
        "average_length_of_words": (
            sum(word_lengths) / len(word_lengths)
            if word_lengths else 0.0
        ),
        "longest_word_length": max(word_lengths, default=0),
        "shortest_word_length": min(word_lengths, default=0),
    }

    return features
