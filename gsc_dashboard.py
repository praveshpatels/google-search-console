# -*- coding: utf-8 -*-
"""
Google Search Console Data Analyzer
Developed by Pravesh Patel
Enhanced & Fixed by ChatGPT
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# Streamlit page settings
st.set_page_config(page_title="GSC Analyzer", page_icon="🔍", layout="wide")
st.title("🔍 Google Search Console Data Analyzer")
st.markdown("*Developed by **Pravesh Patel***", unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader("📁 Upload Google Search Console CSV Export (Performance > Queries or Pages)", type=["csv"])

if uploaded_file:
    # Read and clean the CSV content
    raw_data = uploaded_file.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw_data))

    # Normalize column names (to lowercase, strip spaces)
    df.columns = [col.strip().lower() for col in df.columns]

    # Expected columns in GSC export
    expected_columns = ["query", "clicks", "impressions", "ctr", "position"]
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        st.error(f"❌ Missing columns in CSV: {', '.join(missing)}. Please upload a raw export from GSC (Queries or Pages tab).")
        st.stop()

    # Clean and convert metrics
    for col in ["clicks", "impressions", "ctr", "position"]:
        df[col] = df[col].astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Normalize CTR if in decimals
    if df["ctr"].max() <= 1:
        df["ctr"] *= 100

    # Drop rows with all metrics missing
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

    # KPI Cards
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

    # Top Queries
    st.markdown("### 🔝 Top Queries by Clicks")
    st.dataframe(df.sort_values(by="clicks", ascending=False).head(10), use_container_width=True)

    # CTR vs Position Scatter Plot
    st.markdown("### 📌 CTR vs Average Position")
    fig, ax = plt.subplots()
    ax.scatter(df["position"], df["ctr"], alpha=0.5, c="blue", edgecolors="w")
    ax.set_xlabel("Average Position")
    ax.set_ylabel("CTR (%)")
    ax.set_title("CTR vs Position")
    ax.invert_xaxis()
    ax.grid(True, linestyle="--", alpha=0.4)
    st.pyplot(fig)

    # Opportunity Queries
    st.markdown("### 💡 Opportunity Keywords (Position 5–15, CTR < 5%)")
    opportunities = df[(df["position"] >= 5) & (df["position"] <= 15) & (df["ctr"] < 5)]
    st.dataframe(opportunities.sort_values(by="impressions", ascending=False).head(10), use_container_width=True)

    # Download Button
    st.download_button(
        label="📥 Download Opportunities as CSV",
        data=opportunities.to_csv(index=False),
        file_name="opportunity_keywords.csv",
        mime="text/csv"
    )

else:
    st.info("📌 Please upload a CSV file exported directly from Google Search Console (Performance > Queries or Pages tab).")
