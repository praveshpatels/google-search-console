# -*- coding: utf-8 -*-
"""
Google Search Console Data Analyzer
Enhanced with Smart Table Toggle and Keyword Alert System
Developed by Pravesh Patel
"""

import streamlit as st
import pandas as pd
import io

# Page setup
st.set_page_config(page_title="GSC Analyzer", page_icon="🔍", layout="wide")
st.title("🔍 Google Search Console Data Analyzer")
st.markdown("*Developed by **Pravesh Patel***", unsafe_allow_html=True)

# Sidebar Bio
st.sidebar.markdown("## 👨‍💻 About the Developer")
st.sidebar.markdown("""
Hi, I'm **Pravesh Patel** — a passionate SEO Manager and Data Enthusiast.

🔍 I specialize in SEO, analytics, and tools that simplify Google Search Console data.

💼 I build tools like this to find content opportunities faster.
""")

# File upload
uploaded_file = st.file_uploader("📁 Upload GSC CSV file (Performance > Queries)", type=["csv"])

if uploaded_file:
    # Read and preprocess CSV
    raw_data = uploaded_file.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw_data))

    # Normalize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df.rename(columns={"top_queries": "query"}, inplace=True)

    # Clean numeric data
    for col in ["clicks", "impressions", "position"]:
        df[col] = df[col].astype(str).str.replace(",", "", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["ctr"] = df["ctr"].astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False)
    df["ctr"] = pd.to_numeric(df["ctr"], errors="coerce")

    df.dropna(subset=["clicks", "impressions", "ctr", "position"], how="all", inplace=True)

    # Filter Controls (for KPIs & Top Queries)
    with st.expander("🔍 Filter Data for KPIs & Top Queries"):
        min_impr = st.slider("Minimum Impressions", 0, int(df["impressions"].max()), 0)
        keyword_filter = st.text_input("Filter by Query (Optional)", "")

    # Apply filters
    df_filtered = df.copy()
    if min_impr > 0:
        df_filtered = df_filtered[df_filtered["impressions"] >= min_impr]
    if keyword_filter:
        df_filtered = df_filtered[df_filtered["query"].str.contains(keyword_filter, case=False, na=False)]

    # Guard against empty filter result
    if df_filtered.empty:
        st.warning("⚠️ No rows match the current filters. Please adjust your filter criteria.")
        st.stop()

    # Show raw data
    if st.checkbox("📄 Show Raw Data (Filtered)"):
        row_limit = st.radio("How many rows to display?", options=["Top 100", "Top 500", "All"], index=1)
        if row_limit == "Top 100":
            st.dataframe(df_filtered.head(100), use_container_width=True)
        elif row_limit == "Top 500":
            st.dataframe(df_filtered.head(500), use_container_width=True)
        else:
            st.dataframe(df_filtered, use_container_width=True)

    # KPIs
    st.markdown("### 📊 Overall Performance (Filtered)")
    total_clicks = df_filtered["clicks"].sum()
    total_impressions = df_filtered["impressions"].sum()
    avg_ctr = (df_filtered["ctr"] * df_filtered["impressions"]).sum() / total_impressions if total_impressions else 0
    avg_position = (df_filtered["position"] * df_filtered["impressions"]).sum() / total_impressions if total_impressions else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Clicks", f"{total_clicks:,.0f}")
    col2.metric("Total Impressions", f"{total_impressions:,.0f}")
    col3.metric("Avg. CTR", f"{avg_ctr:.2f}%")
    col4.metric("Avg. Position", f"{avg_position:.2f}")

    # Top Queries
    st.markdown("### 🔝 Top Queries by Clicks (Filtered)")
    st.dataframe(
        df_filtered.sort_values(by="clicks", ascending=False)[
            ["query", "clicks", "impressions", "ctr", "position"]
        ].head(10),
        use_container_width=True
    )

    # Opportunity Keywords
    st.markdown("### 💡 Opportunity Keywords (Position 5–15, CTR < 5%)")
    opportunities = df[(df["position"] >= 5) & (df["position"] <= 15) & (df["ctr"] < 5)]
    st.dataframe(
        opportunities.sort_values(by="impressions", ascending=False).head(10),
        use_container_width=True
    )
    st.download_button(
        label="📥 Download Opportunities as CSV",
        data=opportunities.to_csv(index=False),
        file_name="opportunity_keywords.csv",
        mime="text/csv"
    )

    # Keyword Alerts
    st.markdown("### 🚨 Keyword Alerts (SEO Insights)")

    # 1. Low CTR with High Impressions
    low_ctr_alerts = df[(df["impressions"] > 1000) & (df["ctr"] < 1.0)]
    with st.expander("⚠️ Low CTR (<1%) with High Impressions (>1000)"):
        st.dataframe(
            low_ctr_alerts.sort_values(by="impressions", ascending=False)[
                ["query", "clicks", "impressions", "ctr", "position"]
            ].head(20),
            use_container_width=True
        )

    # 2. Big Impression Surge but Low Clicks
    surge_alerts = df[(df["impressions"] > 1000) & (df["clicks"] < 10) & (df["ctr"] < 1.0)]
    with st.expander("📈 Impression Surge but Low Clicks (<10)"):
        st.dataframe(
            surge_alerts.sort_values(by="impressions", ascending=False)[
                ["query", "clicks", "impressions", "ctr", "position"]
            ].head(20),
            use_container_width=True
        )

    # 3. High CTR but Low Ranking
    booster_alerts = df[(df["ctr"] > 10.0) & (df["position"] > 10)]
    with st.expander("🚀 High CTR (>10%) but Low Ranking (Position >10)"):
        st.dataframe(
            booster_alerts.sort_values(by="ctr", ascending=False)[
                ["query", "clicks", "impressions", "ctr", "position"]
            ].head(20),
            use_container_width=True
        )

else:
    st.info("📌 Please upload a CSV file from Google Search Console > Performance > Queries tab.")
