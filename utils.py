# app/utils.py

import re
from urllib.parse import urlparse, parse_qs, urlencode, quote_plus


AMAZON_IN_DOMAIN = "amazon.in"


def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.replace("\n", " ").split())


def extract_asin_from_url(url: str) -> str | None:
    """
    Extract ASIN from typical Amazon URLs:
    - https://www.amazon.in/dp/B0CHX6NQMD
    - https://www.amazon.in/.../dp/B0CHX6NQMD/ref=...
    - https://www.amazon.in/gp/product/B0CHX6NQMD/...
    """
    if not url:
        return None

    path = urlparse(url).path
    m = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{8,12})", path)
    if m:
        return m.group(1)

    # Fallback: look for B0... pattern anywhere
    m = re.search(r"(B0[A-Z0-9]{8,10})", url)
    return m.group(1) if m else None


def build_amazon_product_url_from_asin(asin: str) -> str:
    asin = asin.strip()
    return f"https://www.{AMAZON_IN_DOMAIN}/dp/{asin}"


def is_amazon_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return AMAZON_IN_DOMAIN in (parsed.netloc or "")
    except Exception:
        return False


def build_google_search_url(query: str) -> str:
    """
    Simple Google search for amazon.in results.
    Example: site:amazon.in Apple iPhone 15 128GB
    """
    q = f"site:{AMAZON_IN_DOMAIN} {query}"
    return f"https://www.google.com/search?q={quote_plus(q)}&num=10"


def parse_price_to_int(price_text: str | None) -> int | None:
    """
    Convert strings like '₹50,990.00' to 50990
    """
    if not price_text:
        return None
    # Keep digits only
    digits = re.sub(r"[^\d]", "", price_text)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def short_list(items, n=3):
    if not items:
        return []
    return items[:n]


def safe_get(d: dict, key: str, default=None):
    v = d.get(key, default)
    return v if v is not None else default
