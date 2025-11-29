# app/scraper.py

import time
import random
import math
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote_plus

import requests
from bs4 import BeautifulSoup

from utils import (
    clean_text,
    extract_asin_from_url,
    build_amazon_product_url_from_asin,
    is_amazon_url,
    parse_price_to_int,
    short_list,
)

BASE_AMAZON_URL = "https://www.amazon.in"

# ------------------------------------------------------------------------
# HTTP helpers
# ------------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def _make_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }


def _get_soup(url: str, retries: int = 3) -> BeautifulSoup:
    """
    Fetch a URL and return BeautifulSoup.
    Retries for transient 5xx errors like 503.
    """
    last_err: Optional[Exception] = None

    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=_make_headers(), timeout=15)

            # Handle transient 5xx errors with retry
            if resp.status_code in (500, 502, 503, 504):
                last_err = RuntimeError(
                    f"Server error {resp.status_code} while fetching {url}"
                )
                time.sleep(1 + attempt)  # backoff
                continue

            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")

        except Exception as e:
            last_err = e
            time.sleep(1 + attempt)

    raise RuntimeError(
        f"Failed to fetch URL after {retries} attempts: {url}\nReason: {last_err}"
    )


# ------------------------------------------------------------------------
# URL normalisation
# ------------------------------------------------------------------------

def _normalize_product_url(url: str) -> str:
    """
    Always convert any Amazon product URL (with tracking / ref params)
    into canonical form: https://www.amazon.in/dp/ASIN

    This avoids weird redirects to search / tracking pages.
    """
    asin = extract_asin_from_url(url)
    if asin:
        return build_amazon_product_url_from_asin(asin)
    # If we can't extract ASIN, fall back to original URL
    return url


# ------------------------------------------------------------------------
# Amazon search helpers (Search results)
# ------------------------------------------------------------------------

def _build_amazon_search_url(keyword: str) -> str:
    q = quote_plus(keyword)
    return f"{BASE_AMAZON_URL}/s?k={q}"


def _search_amazon_products(keyword: str, max_products: int = 10) -> List[str]:
    """
    Use Amazon.in search (s?k=...) to discover product URLs.
    If Amazon blocks us (503 etc.), we return [] instead of crashing.
    """
    search_url = _build_amazon_search_url(keyword)

    try:
        soup = _get_soup(search_url)
    except Exception as e:
        print(f"[WARN] Amazon search failed for {search_url}: {e}")
        return []  # soft fail

    product_urls: List[str] = []
    seen = set()

    for card in soup.select("div[data-component-type='s-search-result']"):
        a = card.select_one(
            "a.a-link-normal.s-no-outline, a.a-link-normal.a-text-normal"
        )
        if not a:
            continue

        href = a.get("href", "")
        if not href or "/dp/" not in href:
            continue

        clean_path = href.split("?")[0]
        full_url = urljoin(BASE_AMAZON_URL, clean_path)

        if not is_amazon_url(full_url) or full_url in seen:
            continue

        seen.add(full_url)
        product_urls.append(full_url)

        if len(product_urls) >= max_products:
            break

    return product_urls


# ------------------------------------------------------------------------
# “Similar products” from product detail page
# ------------------------------------------------------------------------

def _extract_similar_urls_from_product_page(
    product_url: str,
    exclude_asin: Optional[str],
    max_urls: int = 10,
) -> List[str]:
    """
    Look at the product detail page and grab ASINs from
    recommendation carousels (Sponsored, Similar items, etc.).
    If it fails (503 etc.), return [].
    """
    try:
        soup = _get_soup(product_url)
    except Exception as e:
        print(f"[WARN] Similar-product section fetch failed for {product_url}: {e}")
        return []  # soft fail

    asins: List[str] = []
    seen = set()

    for tag in soup.select("li[data-asin], div[data-asin]"):
        asin = tag.get("data-asin")
        if not asin:
            continue
        if exclude_asin and asin == exclude_asin:
            continue
        if asin in seen:
            continue
        seen.add(asin)
        asins.append(asin)
        if len(asins) >= max_urls:
            break

    urls = [build_amazon_product_url_from_asin(a) for a in asins]
    return urls


# ------------------------------------------------------------------------
# Core product parsing
# ------------------------------------------------------------------------

def _parse_product_page(url: str, soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract key information from an Amazon product page."""

    # Title
    title_el = soup.select_one("#productTitle")
    title = clean_text(title_el.get_text()) if title_el else ""

    # Brand / byline
    brand = ""
    brand_el = soup.select_one("#bylineInfo")
    if brand_el:
        brand = clean_text(brand_el.get_text())
    else:
        # fallback: tech spec table
        label_cells = soup.select("#productDetails_techSpec_section_1 th")
        for th in label_cells:
            if "Brand" in th.get_text():
                td = th.find_next("td")
                if td:
                    brand = clean_text(td.get_text())
                    break

    # Price
    price_text = None
    price_el = soup.select_one("span.a-price span.a-offscreen")
    if price_el:
        price_text = price_el.get_text()
    else:
        for selector in [
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
        ]:
            el = soup.select_one(selector)
            if el:
                price_text = el.get_text()
                break

    price_raw = clean_text(price_text) if price_text else None
    price_int = parse_price_to_int(price_raw)

    # Rating
    rating_text = None
    rating_el = soup.select_one("span.a-icon-alt")
    if rating_el:
        rating_text = rating_el.get_text().split()[0]
    try:
        rating = float(rating_text.replace(",", ".")) if rating_text else None
    except Exception:
        rating = None

    # Number of reviews
    num_reviews = None
    rev_el = soup.select_one("#acrCustomerReviewText")
    if rev_el:
        txt = rev_el.get_text()
        digits = "".join(c for c in txt if c.isdigit())
        if digits:
            try:
                num_reviews = int(digits)
            except ValueError:
                num_reviews = None

    # Feature bullets
    features = []
    for li in soup.select("#feature-bullets ul li span.a-list-item"):
        text = clean_text(li.get_text())
        if text:
            features.append(text)
    features = short_list(features, n=5)

    # Variants (e.g. colours)
    variants = []
    for li in soup.select("#variation_color_name li img"):
        alt = li.get("alt")
        if alt:
            alt = clean_text(alt)
            if alt and alt not in variants:
                variants.append(alt)
    variants = short_list(variants, n=6)

    asin = extract_asin_from_url(url)

    product = {
        "asin": asin,
        "url": url,
        "title": title or "",
        "brand": brand or "",
        "price_raw": price_raw,
        "price": price_int,
        "rating": rating,
        "num_reviews": num_reviews,
        "features": features,
        "variants": variants,
    }

    # ✅ sanity check: if nothing parsed, treat as error
    if not product["title"] and product["price"] is None and product["rating"] is None:
        raise RuntimeError(
            "Could not parse product details from page. "
            "Amazon may have returned a non-standard page or blocked the request."
        )

    return product


def fetch_product_from_url(url: str) -> Dict[str, Any]:
    """
    Main entry: always normalise to canonical /dp/ASIN URL first,
    then scrape the product page.
    """
    canonical = _normalize_product_url(url)
    soup = _get_soup(canonical)
    product = _parse_product_page(canonical, soup)
    return product


def fetch_product_from_asin(asin: str) -> Dict[str, Any]:
    url = build_amazon_product_url_from_asin(asin)
    return fetch_product_from_url(url)


def fetch_product_from_name(name: str) -> Dict[str, Any]:
    """
    Use Amazon search to find a suitable amazon.in product for this name.

    We now try multiple search results, because sometimes the first one
    returns a non-standard / blocked page (CAPTCHA, etc.).
    """
    urls = _search_amazon_products(name, max_products=5)
    if not urls:
        raise RuntimeError("No Amazon.in result found for that product name.")

    last_err: Optional[Exception] = None

    # Try each search result until one parses successfully
    for url in urls:
        try:
            return fetch_product_from_url(url)
        except Exception as e:
            last_err = e
            print(f"[WARN] Failed to parse search result {url}: {e}")
            continue

    # If we reach here, none of the candidates worked
    raise RuntimeError(
        f"Could not parse any product from Amazon search results. "
        f"Last error: {last_err}"
    )


# ------------------------------------------------------------------------
# Similarity helpers
# ------------------------------------------------------------------------

_STOPWORDS = {
    "with",
    "for",
    "and",
    "the",
    "inch",
    "cm",
    "gb",
    "green",
    "black",
    "white",
    "blue",
    "phone",
    "smartphone",
    "series",
    "model",
    "new",
}


def _tokenize(text: str) -> set:
    text = text.lower()
    tokens = []
    word = []
    for ch in text:
        if ch.isalnum():
            word.append(ch)
        else:
            if word:
                tokens.append("".join(word))
                word = []
    if word:
        tokens.append("".join(word))

    return {t for t in tokens if t not in _STOPWORDS and len(t) > 1}


def _title_similarity(base_title: str, cand_title: str) -> float:
    base_tokens = _tokenize(base_title)
    cand_tokens = _tokenize(cand_title)
    if not base_tokens or not cand_tokens:
        return 0.0
    inter = len(base_tokens & cand_tokens)
    return inter / len(base_tokens)


# ------------------------------------------------------------------------
# Public: related product detection
# ------------------------------------------------------------------------

def search_similar_products(
    keyword: str,
    max_products: int = 5,
    base_product: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Identify related products using:
    - Similar-product carousels on the base product page
    - Amazon search results (s?k=...)
    - Keyword + brand + title similarity scoring
    Handles 503 and returns [] instead of crashing.
    """

    candidate_urls: List[str] = []
    seen_urls = set()

    # 1️⃣ Similar-product section from base product page
    if base_product and base_product.get("url"):
        base_asin = base_product.get("asin")
        similar_urls = _extract_similar_urls_from_product_page(
            product_url=_normalize_product_url(base_product["url"]),
            exclude_asin=base_asin,
            max_urls=max_products * 2,
        )
        for u in similar_urls:
            if u not in seen_urls:
                seen_urls.add(u)
                candidate_urls.append(u)

    # 2️⃣ Amazon search results
    search_urls = _search_amazon_products(keyword, max_products=max_products * 2)
    for u in search_urls:
        if u not in seen_urls:
            seen_urls.add(u)
            candidate_urls.append(u)

    if not candidate_urls:
        return []

    # 3️⃣ Scrape details for each candidate
    products: List[Dict[str, Any]] = []
    for url in candidate_urls:
        try:
            time.sleep(random.uniform(1, 2.0))
            p = fetch_product_from_url(url)
            if not p.get("title"):
                continue
            products.append(p)
        except Exception as e:
            print(f"[WARN] Failed to fetch related product {url}: {e}")

    if not products:
        return []

    # 4️⃣ Score by similarity + brand + rating + popularity
    base_title = base_product.get("title", "") if base_product else keyword
    base_brand = (base_product.get("brand", "") or "").lower() if base_product else ""

    for p in products:
        title_sim = _title_similarity(base_title, p.get("title", ""))
        brand_match = (
            1.0
            if (base_brand and base_brand in (p.get("brand", "").lower()))
            else 0.0
        )
        rating = p.get("rating") or 0.0
        reviews = p.get("num_reviews") or 0
        pop_term = math.log1p(reviews)

        p["__rel_score"] = (
            0.55 * title_sim
            + 0.20 * brand_match
            + 0.15 * (rating / 5.0)
            + 0.10 * (pop_term / math.log1p(max(1, reviews)))
        )

    products.sort(key=lambda x: x.get("__rel_score", 0.0), reverse=True)

    strong = [p for p in products if p.get("__rel_score", 0.0) >= 0.30]
    if len(strong) < max_products:
        strong = [p for p in products if p.get("__rel_score", 0.0) >= 0.15]
    if len(strong) < max_products:
        strong = products

    # 5️⃣ Remove duplicates and base ASIN
    final: List[Dict[str, Any]] = []
    seen_asins = set()
    base_asin = base_product.get("asin") if base_product else None

    for p in strong:
        asin = p.get("asin")
        if not asin or asin == base_asin:
            continue
        if asin in seen_asins:
            continue
        seen_asins.add(asin)
        final.append(p)
        if len(final) >= max_products:
            break

    return final
