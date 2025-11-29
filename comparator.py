# app/comparator.py

from typing import List, Dict, Any

import pandas as pd

from utils import short_list, safe_get


def build_comparison_table(products: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Build a pandas DataFrame summarizing product comparison.
    Columns: Title, Brand, Price, Rating, Reviews, Features, URL
    """
    rows = []
    for p in products:
        rows.append(
            {
                "ASIN": safe_get(p, "asin", ""),
                "Title": safe_get(p, "title", ""),
                "Brand": safe_get(p, "brand", ""),
                "Price (₹)": safe_get(p, "price", None),
                "Rating": safe_get(p, "rating", None),
                "#Reviews": safe_get(p, "num_reviews", None),
                "Key Features": " • ".join(short_list(safe_get(p, "features", []), 3)),
                "URL": safe_get(p, "url", ""),
            }
        )
    df = pd.DataFrame(rows)

    # Sort: higher rating, more reviews, lower price
    if not df.empty:
        df["Rating"] = df["Rating"].fillna(0)
        df["#Reviews"] = df["#Reviews"].fillna(0)
        df["Price (₹)"] = df["Price (₹)"].fillna(df["Price (₹)"].max() or 0)
        df = df.sort_values(
            by=["Rating", "#Reviews", "Price (₹)"],
            ascending=[False, False, True],
        ).reset_index(drop=True)

    return df


def derive_pros_cons(product: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Very light-weight pros/cons generator for display.
    """
    pros: List[str] = []
    cons: List[str] = []

    rating = product.get("rating") or 0
    reviews = product.get("num_reviews") or 0
    price = product.get("price")
    features = product.get("features") or []

    if rating >= 4.3:
        pros.append("Highly rated by buyers")
    elif rating >= 4.0:
        pros.append("Good overall rating")

    if reviews > 5000:
        pros.append("Very popular (5K+ reviews)")
    elif reviews > 1000:
        pros.append("Popular product")

    if price is not None:
        pros.append(f"Price around ₹{price:,}")

    if features:
        pros.extend(short_list(features, 2))

    # Simple cons based on rating
    if rating and rating < 4.0:
        cons.append("Rating below 4.0 — check reviews carefully")

    return {"pros": short_list(pros, 3), "cons": short_list(cons, 3)}
