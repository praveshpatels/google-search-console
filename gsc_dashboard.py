# -*- coding: utf-8 -*-
"""
Google Search Console Data Analyzer
Supports both Queries and Pages CSV exports.
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
uploaded_file = st.file_uploader("📁 Upload GSC CSV Export (Performance > Queries or Pages)", type=["csv"])

if uploaded_file:
    raw_data = uploaded_file.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw_data))

    # Normalize column names
    df.columns = [col.strip().lower() for col in df.columns]

    # Detect whether it's Queries or Pages export
    if "query" in df.columns:
        keyword_col = "query"
        title_label = "Queries"
    elif "page" in df.columns:
        keyword_col = "page"
        title_label = "Pages"
    else:
        st.error("❌ CSV must contain either a 'Query' or 'Page' column.")
        st.stop()

    # Clean & convert core metrics
    for col in ["clicks", "impressions", "ctr", "position"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            st.error(f"❌ Missing expected column: {col}")
            st.stop()

    # Normalize CTR to percentage
    if df["ctr"].max() <= 1:
        df["ctr"] *= 100

    # Remove rows with all metric data missing
    df.dropna(subset=["clicks", "impressions", "ctr", "position"], how="all", inplace=True)

    # Filtering
    with st.expander("🔍 Filter Data"):
        min_impr = st.slider("Minimum Impressions", 0, int(df["impressions"].max()), 100)
        keyword_filter = st.text_input(f"Filter by {title_label[:-1]} (Optional)", "")
        df = df[df["impressions"] >= min_impr]
        if keyword_filter:
            df = df[df[keyword_col].str.contains(keyword_filter, case=False, na=False)]

    # Show raw data
    if st.checkbox("📄 Show Raw Data"):
        st.dataframe(df.head(25), use_container_width=True)

    # KPIs
    st.markdown("### 📊 Overall Performance")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Clicks", f"{df['clicks'].sum():,.0f}")
    col2.metric("Total Impressions", f"{df['impressions'].sum():,.0f}")
    col3.metric("Avg. CTR", f"{df['ctr'].mean():.2f}%")
    col4.metric("Avg. Position", f"{df['position'].mean():.2f}")

    # Top Queries or Pages
    st.markdown(f"### 🔝 Top {title_label} by Clicks")
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

    # Opportunities
    st.markdown("### 💡 Opportunity Keywords (Position 5–15, CTR < 5%)")
    opportunities = df[(df["position"] >= 5) & (df["position"] <= 15) & (df["ctr"] < 5)]
    st.dataframe(opportunities.sort_values(by="impressions", ascending=False).head(10), use_container_width=True)

    st.download_button(
        label="📥 Download Opportunities as CSV",
        data=opportunities.to_csv(index=False),
        file_name="opportunity_keywords.csv",
        mime="text/csv"
    )

else:
    st.info("📌 Please upload a CSV file exported from Google Search Console (Performance > Queries or Pages tab).")
