# -*- coding: utf-8 -*-
"""
Google Search Console Data Analyzer (Queries CSV)
Compatible with Excel-exported CSV files.
Developed by Pravesh Patel
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# Page settings
st.set_page_config(page_title="GSC Analyzer", page_icon="🔍", layout="wide")
st.title("🔍 Google Search Console Data Analyzer")
st.markdown("*Developed by **Pravesh Patel***", unsafe_allow_html=True)

# File upload
uploaded_file = st.file_uploader("📁 Upload GSC Queries CSV file (from Performance > Queries)", type=["csv"])

if uploaded_file:
    # Read CSV content
    raw_data = uploaded_file.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw_data))

    # Normalize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Rename to standard internal names
    df.rename(columns={
        "top_queries": "query",
        "impressio": "impressions"  # Just in case of typo
    }, inplace=True)

    # Check required columns
    required_cols = ["query", "clicks", "impressions", "ctr", "position"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
        st.stop()

    # Clean numeric fields
    for col in ["clicks", "impressions", "position"]:
        df[col] = df[col].astype(str).str.replace(",", "", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Clean CTR: strip '%' only, no multiplication
    df["ctr"] = df["ctr"].astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False)
    df["ctr"] = pd.to_numeric(df["ctr"], errors="coerce")

    # Drop rows with missing metrics
    df.dropna(subset=["clicks", "impressions", "ctr", "position"], how="all", inplace=True)

    # Filters
    with st.expander("🔍 Filter Data"):
        min_impr = st.slider("Minimum Impressions", 0, int(df["impressions"].max()), 100)
        keyword_filter = st.text_input("Filter by Query (Optional)", "")
        df = df[df["impressions"] >= min_impr]
        if keyword_filter:
            df = df[df["query"].str.contains(keyword_filter, case=False, na=False)]

    # Show raw data
    if st.checkbox("📄 Show Raw Data"):
        st.dataframe(df.head(25), use_container_width=True)

    # KPIs
    total_clicks = df["clicks"].sum()
    total_impressions = df["impressions"].sum()
    avg_ctr = df["ctr"].mean()
    avg_position = df["position"].mean()

    st.markdown("### 📊 Overall Performance")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Clicks", f"{total_clicks:,.0f}")
    col2.metric("Total Impressions", f"{total_impressions:,.0f}")
    col3.metric("Avg. CTR", f"{avg_ctr:.2f}%")
    col4.metric("Avg. Position", f"{avg_position:.2f}")

    # Top queries
    st.markdown("### 🔝 Top Queries by Clicks")
    st.dataframe(df.sort_values(by="clicks", ascending=False).head(10), use_container_width=True)

    # CTR vs Position
    st.markdown("### 📌 CTR vs Average Position")
    fig, ax = plt.subplots()
    ax.scatter(df["position"], df["ctr"], alpha=0.5, c="blue", edgecolors="w")
    ax.set_xlabel("Average Position")
    ax.set_ylabel("CTR (%)")
    ax.set_title("CTR vs Position")
    ax.invert_xaxis()
    ax.grid(True, linestyle="--", alpha=0.4)
    st.pyplot(fig)

    # Opportunity keywords
    st.markdown("### 💡 Opportunity Keywords (Position 5–15, CTR < 5%)")
    opportunities = df[(df["position"] >= 5) & (df["position"] <= 15) & (df["ctr"] < 5)]
    st.dataframe(opportunities.sort_values(by="impressions", ascending=False).head(10), use_container_width=True)

    # Download CSV
    st.download_button(
        label="📥 Download Opportunities as CSV",
        data=opportunities.to_csv(index=False),
        file_name="opportunity_keywords.csv",
        mime="text/csv"
    )

else:
    st.info("📌 Please upload the CSV file from Google Search Console (Performance > Queries tab).")
