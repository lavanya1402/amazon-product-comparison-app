# app/recommender.py

from typing import List, Dict, Any

import math

from utils import safe_get


def _score_product(p: Dict[str, Any], max_price: float, max_reviews: float) -> float:
    """
    Composite score based on:
    - rating (0–5)
    - #reviews (popularity)
    - price (lower is better)
    """
    rating = safe_get(p, "rating", 0.0) or 0.0
    reviews = float(safe_get(p, "num_reviews", 0) or 0)
    price = float(safe_get(p, "price", max_price) or max_price)

    # Normalize
    rating_norm = rating / 5.0
    reviews_norm = math.log1p(reviews) / math.log1p(max_reviews) if max_reviews else 0.0
    price_norm = 1.0 - (price / max_price) if max_price else 0.0  # cheaper = better

    # Weights: tune as desired
    score = 0.5 * rating_norm + 0.3 * reviews_norm + 0.2 * price_norm
    return score


def recommend_best(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Return (best_product, explanation_text).
    """
    if not products:
        return {"product": None, "reason": "No products available for recommendation."}

    max_price = max([p.get("price") or 0 for p in products]) or 1.0
    max_reviews = max([p.get("num_reviews") or 0 for p in products]) or 1.0

    best = None
    best_score = -1.0

    for p in products:
        score = _score_product(p, max_price, max_reviews)
        p["__score"] = score
        if score > best_score:
            best_score = score
            best = p

    if not best:
        return {"product": None, "reason": "Unable to compute a clear winner."}

    title = safe_get(best, "title", "This product")
    price = safe_get(best, "price", None)
    rating = safe_get(best, "rating", None)
    reviews = safe_get(best, "num_reviews", None)

    reasons = []
    if rating:
        reasons.append(f"high rating of {rating:.1f}★")
    if reviews:
        reasons.append(f"{reviews:,} customer reviews")
    if price:
        reasons.append(f"competitive price (~₹{price:,})")

    reason_text = (
        f"We recommend **{title}** as the best overall value because it combines "
        + ", ".join(reasons)
        + "."
    )

    return {"product": best, "reason": reason_text}
