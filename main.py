# main.py
# -------------------------------------------------------------
# Amazon Product Comparison (AI Powered)
# End-to-end Streamlit app with filters, ranking chart & CSV export
# -------------------------------------------------------------

from typing import List, Dict, Any, Optional

import pandas as pd
import streamlit as st
import altair as alt

from scraper import (
    fetch_product_from_url,
    fetch_product_from_asin,
    fetch_product_from_name,
    search_similar_products,
)

# -------------------------------------------------------------
# Small helpers
# -------------------------------------------------------------


def _looks_like_amazon_url(text: str) -> bool:
    """Rough check: is this an Amazon product URL?"""
    text = (text or "").strip().lower()
    return text.startswith("http") and "amazon." in text and "/dp/" in text


def _looks_like_asin(text: str) -> bool:
    """Simple ASIN check: 10 alphanumeric chars."""
    text = (text or "").strip()
    return len(text) == 10 and text.isalnum()


def _product_list_to_df(products: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert list of product dicts (from scraper) into a clean DataFrame
    ready for display & analysis.

    Expected keys: asin, title, brand, price, rating, num_reviews,
                   features, url, and optional __rel_score.
    """
    rows = []
    for p in products:
        rows.append(
            {
                "ASIN": p.get("asin", ""),
                "Title": p.get("title", ""),
                "Brand": p.get("brand", ""),
                "Price (₹)": p.get("price"),
                "Rating": p.get("rating"),
                "#Reviews": p.get("num_reviews"),
                "Key Features": "; ".join(p.get("features", [])),
                "URL": p.get("url", ""),
                "SimilarityScore": round(p.get("__rel_score", 0.0), 2),
            }
        )

    df = pd.DataFrame(rows)

    # Ensure numeric types
    if not df.empty:
        df["Price (₹)"] = pd.to_numeric(df["Price (₹)"], errors="coerce")
        df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
        df["#Reviews"] = pd.to_numeric(df["#Reviews"], errors="coerce")

    return df


def _build_pros_cons(
    product: Dict[str, Any],
    all_prices: pd.Series,
    all_ratings: pd.Series,
) -> Dict[str, List[str]]:
    """Generate simple pros / cons based on rating, reviews & price."""
    pros: List[str] = []
    cons: List[str] = []

    rating = product.get("rating") or 0.0
    reviews = product.get("num_reviews") or 0
    price = product.get("price")

    median_price = all_prices.median() if not all_prices.empty else price
    median_rating = all_ratings.median() if not all_ratings.empty else rating

    # --- Pros
    if rating >= 4.4:
        pros.append("Highly rated by buyers")
    elif rating >= 4.0:
        pros.append("Good overall rating")

    if reviews >= 5000:
        pros.append("Very popular (5K+ reviews)")
    elif reviews >= 1000:
        pros.append("Reasonable number of reviews")

    if price is not None:
        pros.append(f"Price around ₹{price:,}")

    # --- Cons
    if rating and median_rating and rating < median_rating:
        cons.append("Rating is lower than some alternatives")

    if price and median_price and price > median_price:
        cons.append("Relatively expensive compared to similar options")

    if not cons:
        cons.append("No major drawbacks identified from available data")

    return {"pros": pros, "cons": cons}


def _choose_best_product(df: pd.DataFrame) -> Optional[pd.Series]:
    """
    Simple heuristic (kept for reference, not used in final score):
    1. Highest rating
    2. Then highest #reviews
    3. Then lowest price
    """
    if df.empty:
        return None

    temp = df.copy()
    temp["Rating_fill"] = temp["Rating"].fillna(0)
    temp["Reviews_fill"] = temp["#Reviews"].fillna(0)
    temp["Price_fill"] = temp["Price (₹)"].fillna(temp["Price (₹)"].max())

    temp = temp.sort_values(
        by=["Rating_fill", "Reviews_fill", "Price_fill"],
        ascending=[False, False, True],
        kind="mergesort",
    )
    return temp.iloc[0]


def _norm(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Min–max normalisation helper."""
    if series.empty:
        return series
    mx, mn = series.max(), series.min()
    if mx == mn:
        return pd.Series(1.0, index=series.index)
    if higher_is_better:
        return (series - mn) / (mx - mn)
    else:
        return (mx - series) / (mx - mn)


# -------------------------------------------------------------
# Main application
# -------------------------------------------------------------


def main():
    st.set_page_config(
        page_title="Amazon Product Comparison (AI Powered)",
        page_icon="🛒",
        layout="wide",
    )

    st.title("Amazon Product Comparison (AI Powered) 🛒")
    st.caption("Built by Lavanya Srivastava — powered by Python + Streamlit")

    with st.expander("How to use this app", expanded=False):
        st.markdown(
            """
            **Steps**

            1. Choose input type — **Product name**, **ASIN** or **Amazon URL**  
            2. Enter value and click **“Analyze / Compare Products”**  
            3. The app will:

               - Fetch the base product from Amazon.in  
               - Discover up to **5 similar products**  
               - Build a **comparison table** with at least 5 factors  
               - Show an **overall score chart** (Price + Rating)  
               - Generate **Pros & Cons** and **one final recommendation**
            """
        )

    # ---------------------------------------------------------
    # Input section
    # ---------------------------------------------------------

    st.subheader("Choose input type:")

    col_method, col_value = st.columns([1, 3])

    with col_method:
        input_method = st.radio(
            "Input method",
            options=["Product Name", "ASIN", "Amazon URL"],
            horizontal=False,
        )

    with col_value:
        default_placeholder = {
            "Product Name": "e.g. Sony WH-1000XM5",
            "ASIN": "e.g. B09XS7JWHH",
            "Amazon URL": "Paste full Amazon.in product URL here",
        }[input_method]

        user_value = st.text_input("Enter value", placeholder=default_placeholder)

    analyze_clicked = st.button("Analyze / Compare Products", type="primary")

    if not analyze_clicked:
        st.stop()

    raw_value = user_value.strip()
    if not raw_value:
        st.error("Please enter a value before running the comparison.")
        st.stop()

    # ---------------------------------------------------------
    # Decide effective method (auto-detect URL / ASIN if pasted under wrong option)
    # ---------------------------------------------------------
    effective_method = input_method

    if input_method == "Product Name":
        if _looks_like_amazon_url(raw_value):
            effective_method = "Amazon URL"
            st.info("Detected an Amazon URL — treating input as **Amazon URL**.")
        elif _looks_like_asin(raw_value):
            effective_method = "ASIN"
            st.info("Detected an ASIN — treating input as **ASIN**.")

    elif input_method == "Amazon URL":
        if _looks_like_asin(raw_value):
            effective_method = "ASIN"
            st.info("Input looks like an ASIN — treating as **ASIN**.")
        elif not _looks_like_amazon_url(raw_value):
            st.warning(
                "Input does not look like a typical Amazon product URL "
                "(for example: https://www.amazon.in/dp/B09XS7JWHH)."
            )

    # ---------------------------------------------------------
    # Fetch base product (with ASIN fallback via URL if needed)
    # ---------------------------------------------------------

    try:
        if effective_method == "Product Name":
            base_product = fetch_product_from_name(raw_value)

        elif effective_method == "ASIN":
            # First try dedicated ASIN scraper
            try:
                base_product = fetch_product_from_asin(raw_value)
            except Exception:
                # Fallback: construct URL from ASIN
                fallback_url = f"https://www.amazon.in/dp/{raw_value}"
                base_product = fetch_product_from_url(fallback_url)

        else:  # Amazon URL
            base_product = fetch_product_from_url(raw_value)

    except Exception as e:
        if effective_method == "Amazon URL":
            st.error(
                "Could not fetch base product from the Amazon URL.\n\n"
                "Please make sure it is a valid **Amazon.in product link** "
                "(e.g., https://www.amazon.in/dp/B09XS7JWHH).\n\n"
                f"Details: {e}"
            )
        elif effective_method == "ASIN":
            st.error(
                "Could not fetch base product using the ASIN provided.\n\n"
                "Please check the ASIN (10 characters, letters+numbers).\n\n"
                f"Details: {e}"
            )
        else:
            st.error(
                "Could not fetch base product using the product name.\n\n"
                "Tip: Try using the exact **ASIN** or full **Amazon URL** "
                "if product name search fails.\n\n"
                f"Details: {e}"
            )
        st.stop()

    # ---------------------------------------------------------
    # Fetch related products (aggressive search + fallback)
    # ---------------------------------------------------------

    keyword = base_product.get("title") or raw_value
    brand = (base_product.get("brand") or "").strip()

    related_products: List[Dict[str, Any]] = []

    def _add_unique_results(results: List[Dict[str, Any]]) -> None:
        """Extend related_products with new ASIN/title combinations only."""
        nonlocal related_products
        seen_asins = {base_product.get("asin", "")}
        seen_titles = {str(base_product.get("title", "")).strip().lower()}
        for p in related_products:
            seen_asins.add(p.get("asin", ""))
            seen_titles.add(str(p.get("title", "")).strip().lower())

        for p in results:
            asin = p.get("asin", "")
            title = str(p.get("title", "")).strip().lower()
            if asin and asin in seen_asins:
                continue
            if title and title in seen_titles:
                continue
            related_products.append(p)
            seen_asins.add(asin)
            seen_titles.add(title)
            if len(related_products) >= 4:  # base + 4 = 5 total
                break

    with st.spinner("Fetching related products from Amazon.in ..."):
        try:
            # 1️⃣ Full title search – higher max_products for better coverage
            res1 = search_similar_products(
                keyword=keyword,
                max_products=15,
                base_product=base_product,
            )
        except Exception:
            res1 = []
        _add_unique_results(res1)

        # 2️⃣ Shorter keyword (first 4 words)
        if len(related_products) < 4:
            short_kw = " ".join(str(keyword).split()[:4])
            if short_kw and short_kw.lower() != str(keyword).lower():
                try:
                    res2 = search_similar_products(
                        keyword=short_kw,
                        max_products=15,
                        base_product=base_product,
                    )
                except Exception:
                    res2 = []
                _add_unique_results(res2)

        # 3️⃣ Brand + main keyword (for categories like headphones)
        if len(related_products) < 4 and brand:
            combo_kw = f"{brand} {short_kw or keyword}"
            try:
                res3 = search_similar_products(
                    keyword=combo_kw,
                    max_products=15,
                    base_product=base_product,
                )
            except Exception:
                res3 = []
            _add_unique_results(res3)

    if not related_products:
        st.warning(
            "Base product fetched successfully, but no strong related products were "
            "found. Showing only the base product."
        )

    # Always keep at most 4 related + 1 base = 5 total
    all_products = [base_product] + related_products[:4]

    # ---------------------------------------------------------
    # Convert to DataFrame
    # ---------------------------------------------------------

    comparison_df = _product_list_to_df(all_products)

    if comparison_df.empty:
        st.error("No comparable product data available.")
        st.stop()

    st.success("Base product fetched successfully ✅")

    # ---------------------------------------------------------
    # Filters section (simple & business-friendly)
    # ---------------------------------------------------------

    st.subheader("Filters")

    price_min = int(comparison_df["Price (₹)"].min() or 0)
    price_max = int(comparison_df["Price (₹)"].max() or 0)
    rating_min = float(comparison_df["Rating"].min() or 0.0)
    rating_max = float(comparison_df["Rating"].max() or 5.0)
    reviews_max = int(comparison_df["#Reviews"].max() or 0)

    c1, c2, c3 = st.columns(3)

    with c1:
        max_budget = st.slider(
            "Maximum budget (₹)",
            min_value=price_min,
            max_value=price_max,
            value=price_max,
            step=1000,
        )

    with c2:
        default_rating = 4.0 if rating_max >= 4.0 else round(rating_min, 1)
        min_rating = st.slider(
            "Minimum rating",
            min_value=0.0,
            max_value=5.0,
            value=default_rating,
            step=0.1,
        )

    with c3:
        min_reviews = st.slider(
            "Minimum number of reviews",
            min_value=0,
            max_value=reviews_max,
            value=min(1000, reviews_max),
            step=100,
        )

    # Apply filters
    filtered_df = comparison_df.copy()
    filtered_df = filtered_df[
        (filtered_df["Price (₹)"].fillna(price_max) <= max_budget)
        & (filtered_df["Rating"].fillna(0.0) >= min_rating)
        & (filtered_df["#Reviews"].fillna(0) >= min_reviews)
    ]

    if filtered_df.empty:
        st.warning(
            "No products match the current filters. Filters reset to show all products."
        )
        filtered_df = comparison_df.copy()

    # Stable order; ranking will be done by score
    filtered_df = filtered_df.sort_values(
        by=["Title"],
        ascending=[True],
        kind="mergesort",
    )

    # ---------------------------------------------------------
    # Compute overall score (ONLY Price & Rating)
    # ---------------------------------------------------------

    score_df = filtered_df[["Title", "Price (₹)", "Rating"]].dropna()

    if not score_df.empty:
        score_df["rating_norm"] = _norm(score_df["Rating"], True)
        score_df["price_norm"] = _norm(score_df["Price (₹)"], False)

        # Overall score (0–100) — weights: Rating 70%, Price 30%
        score_df["OverallScore"] = (
            0.7 * score_df["rating_norm"] + 0.3 * score_df["price_norm"]
        ) * 100

        score_df = score_df.sort_values("OverallScore", ascending=False)
        best_title = score_df.iloc[0]["Title"]
    else:
        best_title = None

    # ---------------------------------------------------------
    # Comparison Table (assignment style)
    # ---------------------------------------------------------

    st.subheader("📊 Comparison Table")

    display_df = filtered_df.copy()

    display_df["Product Name"] = display_df["Title"]
    display_df["Price"] = display_df["Price (₹)"].apply(
        lambda x: f"₹{int(x):,}" if pd.notnull(x) else "N/A"
    )
    display_df["Rating_display"] = display_df["Rating"].round(1)
    display_df["Reviews"] = display_df["#Reviews"].apply(
        lambda x: f"{int(x):,}" if pd.notnull(x) else "N/A"
    )
    display_df["Key Feature"] = display_df["Key Features"].apply(
        lambda t: t.split(";")[0] if isinstance(t, str) and t else ""
    )

    pretty_table = display_df[
        ["Product Name", "Price", "Rating_display", "Reviews", "Key Feature"]
    ].rename(columns={"Rating_display": "Rating"})

    st.dataframe(pretty_table, use_container_width=True)

    csv_bytes = pretty_table.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download comparison as CSV",
        data=csv_bytes,
        file_name="amazon_product_comparison.csv",
        mime="text/csv",
    )

    # ---------------------------------------------------------
    # Overall Score Bar Chart – 1 bar per product (Price + Rating only)
    # ---------------------------------------------------------

    st.subheader("📊 Overall Score (Price + Rating)")

    if not score_df.empty:
        viz_df = score_df[
            ["Title", "OverallScore", "Price (₹)", "Rating"]
        ].copy()

        viz_df["BestFlag"] = viz_df["Title"].apply(
            lambda t: "Recommended" if t == best_title else "Other"
        )

        chart = (
            alt.Chart(viz_df)
            .mark_bar()
            .encode(
                x=alt.X(
                    "Title:N",
                    title="Product",
                    axis=alt.Axis(labelAngle=-35),
                ),
                y=alt.Y(
                    "OverallScore:Q",
                    title="Overall score (0–100)",
                    scale=alt.Scale(domain=[0, 100]),
                ),
                color=alt.Color(
                    "BestFlag:N",
                    scale=alt.Scale(
                        domain=["Recommended", "Other"],
                        range=["#d62728", "#7f7f7f"],  # red for best, grey for others
                    ),
                    legend=alt.Legend(title="Recommendation"),
                ),
                tooltip=[
                    alt.Tooltip("Title:N", title="Product"),
                    alt.Tooltip("OverallScore:Q", title="Score", format=".1f"),
                    alt.Tooltip("Price (₹):Q", title="Price (₹)", format=","),
                    alt.Tooltip("Rating:Q", title="Rating", format=".1f"),
                ],
            )
            .properties(
                height=400,
                title="Overall ranking based on Rating (higher) and Price (lower)",
            )
            .configure_axis(labelFontSize=12, titleFontSize=13)
        )

        st.altair_chart(chart, use_container_width=True)

    # ---------------------------------------------------------
    # Raw data (debug) in an expander only
    # ---------------------------------------------------------

    with st.expander("🧾 Raw product dictionary data (debug view)", expanded=False):
        st.json(all_products)

    # ---------------------------------------------------------
    # Pros & Cons + Recommendation
    # ---------------------------------------------------------

    st.subheader("Quick Pros & Cons")

    price_series = comparison_df["Price (₹)"]
    rating_series = comparison_df["Rating"]

    for p in all_products:
        title = p.get("title", "Unknown product")
        with st.expander(title, expanded=False):
            pc = _build_pros_cons(p, price_series, rating_series)
            cols = st.columns(2)
            with cols[0]:
                st.markdown("**Pros**")
                for item in pc["pros"]:
                    st.markdown(f"- {item}")
            with cols[1]:
                st.markdown("**Cons**")
                for item in pc["cons"]:
                    st.markdown(f"- {item}")

            st.markdown(
                f"[View on Amazon]({p.get('url','')})",
                help="Opens the product page on Amazon.in",
            )

    # Final recommendation – consistent with score chart
    st.subheader("🏆 Final Recommendation")

    if best_title is None:
        st.info("Not enough data to choose a clear winner.")
    else:
        best_full_row = filtered_df[filtered_df["Title"] == best_title].iloc[0]
        price = best_full_row["Price (₹)"]
        rating = best_full_row["Rating"]
        reviews = int(best_full_row["#Reviews"] or 0)
        url = best_full_row["URL"]
        score_value = float(
            score_df[score_df["Title"] == best_title]["OverallScore"].iloc[0]
        )

        st.markdown(
            f"We recommend **{best_title}** as the best overall value.\n\n"
            f"- Overall score (Price + Rating): **{score_value:.1f}/100**\n"
            f"- Rating: **{rating:.1f}★** with **{reviews:,}** reviews\n"
            f"- Approx. price: **₹{price:,}**"
        )
        st.markdown(f"[Open recommended product on Amazon]({url})")


# -------------------------------------------------------------
# Entry point
# -------------------------------------------------------------

if __name__ == "__main__":
    main()
