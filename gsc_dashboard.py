# -*- coding: utf-8 -*-
"""
Google Search Console Data Analyzer (Enhanced Version)
Includes:
- KPI metrics
- Top queries
- Opportunity keywords
- Alerts Dashboard (color-coded + human-readable rules)
- Developer bio
Developed by Pravesh Patel
"""

import streamlit as st
import pandas as pd
import numpy as np
import io

# Page setup
st.set_page_config(page_title="GSC Data Analyzer", page_icon="🔍", layout="wide")
st.title("🔍 Google Search Console Data Analyzer")
st.markdown("*Developed by **Pravesh Patel***", unsafe_allow_html=True)

# Sidebar: About the Developer
st.sidebar.markdown("## 👨‍💻 About the Developer")
st.sidebar.markdown("""
Hi, I'm **Pravesh Patel** — a passionate SEO Manager and data enthusiast.

🔍 I specialize in search engine optimization, digital analytics, and building intuitive tools that help marketers make better decisions using real data.

💼 Currently working at Blow Horn Media, I also create tools like this one to simplify GSC analysis and uncover content opportunities.

📬 [Visit praveshpatel.com](https://www.praveshpatel.com)
""")

# Upload file
uploaded_file = st.file_uploader("📁 Upload GSC CSV file (Performance > Queries)", type=["csv"])

if uploaded_file:
    # Read and parse CSV
    raw_data = uploaded_file.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw_data))

    # Normalize columns
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df.rename(columns={"top_queries": "query"}, inplace=True)

    required_cols = ["query", "clicks", "impressions", "ctr", "position"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"❌ Missing columns: {', '.join(missing)}")
        st.stop()

    # Clean numeric values
    for col in ["clicks", "impressions", "position"]:
        df[col] = df[col].astype(str).str.replace(",", "", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["ctr"] = df["ctr"].astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False)
    df["ctr"] = pd.to_numeric(df["ctr"], errors="coerce")

    df.dropna(subset=["clicks", "impressions", "ctr", "position"], how="all", inplace=True)

    # Filter controls
    with st.expander("🔍 Filter Data"):
        min_impr = st.slider("Minimum Impressions", 0, int(df["impressions"].max()), 100)
        keyword_filter = st.text_input("Filter by Query (Optional)", "")
        df = df[df["impressions"] >= min_impr]
        if keyword_filter:
            df = df[df["query"].str.contains(keyword_filter, case=False, na=False)]

    # Smart raw data table
    if st.checkbox("📄 Show Raw Data"):
        row_limit = st.radio("How many rows to display?", options=["Top 100", "Top 500", "All"], index=1)
        if row_limit == "Top 100":
            st.dataframe(df.head(100), use_container_width=True)
        elif row_limit == "Top 500":
            st.dataframe(df.head(500), use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

    # Weighted metrics
    total_clicks = df["clicks"].sum()
    total_impressions = df["impressions"].sum()
    avg_ctr = (df["ctr"] * df["impressions"]).sum() / total_impressions if total_impressions else 0
    avg_position = (df["position"] * df["impressions"]).sum() / total_impressions if total_impressions else 0

    # Display KPIs
    st.markdown("### 📊 Overall Performance")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Clicks", f"{total_clicks:,.0f}")
    col2.metric("Total Impressions", f"{total_impressions:,.0f}")
    col3.metric("Avg. CTR", f"{avg_ctr:.2f}%")
    col4.metric("Avg. Position", f"{avg_position:.2f}")

    # ========================
    # 🔔 Alerts Dashboard (Enhanced with Descriptions)
    # ========================
    st.markdown("### 🔔 Alerts Dashboard (SEO Performance Signals)")

    # Define alerts
    critical_drops = df[(df["ctr"] < 1.0) & (df["impressions"] > 1000)]
    warnings = df[(df["impressions"] > 1000) & (df["clicks"] < 10)]
    wins = df[(df["ctr"] > 10.0) & (df["position"] > 10)]

    # Summary Cards
    col1, col2, col3 = st.columns(3)
    col1.metric("🔴 Critical Issues", f"{len(critical_drops):,}")
    col2.metric("🟠 Warnings", f"{len(warnings):,}")
    col3.metric("🟢 Potential Wins", f"{len(wins):,}")

    # Critical Issues
    with st.expander("🔴 View Critical Issues"):
        st.markdown("**Low CTR (<1%) with High Impressions (>1000)**")
        if critical_drops.empty:
            st.info("No critical issues found.")
        else:
            st.dataframe(
                critical_drops.sort_values(by="impressions", ascending=False)[
                    ["query", "clicks", "impressions", "ctr", "position"]
                ],
                use_container_width=True
            )

    # Warnings
    with st.expander("🟠 View Warning Keywords"):
        st.markdown("**Impression Surge but Low Clicks (<10)**")
        if warnings.empty:
            st.info("No warning keywords found.")
        else:
            st.dataframe(
                warnings.sort_values(by="impressions", ascending=False)[
                    ["query", "clicks", "impressions", "ctr", "position"]
                ],
                use_container_width=True
            )

    # Wins
    with st.expander("🟢 View High-CTR, Low-Rank Wins"):
        st.markdown("**High CTR (>10%) but Low Ranking (Position >10)**")
        if wins.empty:
            st.info("No opportunity wins found.")
        else:
            st.dataframe(
                wins.sort_values(by="ctr", ascending=False)[
                    ["query", "clicks", "impressions", "ctr", "position"]
                ],
                use_container_width=True
            )

    # Top Queries
    st.markdown("### 🔝 Top Queries by Clicks")
    st.dataframe(
        df.sort_values(by="clicks", ascending=False)[["query", "clicks", "impressions", "ctr", "position"]].head(10),
        use_container_width=True
    )

    # Opportunity keywords — filtered display and CSV export
    st.markdown("### 💡 Opportunity Keywords (Position 5–15, CTR < 5%)")
    opportunities = df[(df["position"] >= 5) & (df["position"] <= 15) & (df["ctr"] < 5)]
    st.markdown(f"🔢 Total Opportunity Keywords Found: **{len(opportunities):,}**")

    if not opportunities.empty:
        st.dataframe(
            opportunities.sort_values(by="impressions", ascending=False),
            use_container_width=True
        )

        st.download_button(
            label="📥 Download Opportunities as CSV",
            data=opportunities.to_csv(index=False),
            file_name="opportunity_keywords.csv",
            mime="text/csv"
        )
    else:
        st.info("No opportunity keywords found based on the current filters.")

else:
    st.info("📌 Please upload a CSV file from Google Search Console > Performance > Queries tab.")
