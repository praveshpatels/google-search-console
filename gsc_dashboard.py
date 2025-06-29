# -*- coding: utf-8 -*-
"""
Google Search Console Data Analyzer
Developed by Pravesh Patel
Enhanced by ChatGPT
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Page config
st.set_page_config(page_title="GSC Analyzer", page_icon="🔍", layout="wide")
st.title("🔍 Google Search Console Data Analyzer")
st.markdown("*Developed by **Pravesh Patel***", unsafe_allow_html=True)

# File upload
uploaded_file = st.file_uploader("📁 Upload GSC CSV Export (Performance > Queries or Pages)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Normalize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Fallback for known alternate column names
    column_mapping = {
        "ctr": ["ctr", "click-through_rate"],
        "position": ["position", "avg_position"],
    }

    for key, variants in column_mapping.items():
        for variant in variants:
            if variant in df.columns:
                df[key] = df[variant]
                break

    # Clean numeric columns
    for col in ["clicks", "impressions", "ctr", "position"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Normalize CTR if not in %
    if df['ctr'].max() <= 1:
        df['ctr'] *= 100

    # Optional filters
    with st.expander("🔍 Filter Data"):
        min_impr = st.slider("Minimum Impressions", 0, int(df['impressions'].max()), 100)
        search_col = None
        for col in ['query', 'page']:
            if col in df.columns:
                search_col = col
                break
        keyword_filter = st.text_input(f"Filter by {search_col.capitalize()} Contains", "") if search_col else None

        if search_col and keyword_filter:
            df = df[df[search_col].str.contains(keyword_filter, case=False, na=False)]
        df = df[df["impressions"] >= min_impr]

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
    col1.metric("Total Clicks", f"{total_clicks:,}")
    col2.metric("Total Impressions", f"{total_impressions:,}")
    col3.metric("Avg. CTR", f"{avg_ctr:.2f}%")
    col4.metric("Avg. Position", f"{avg_position:.2f}")

    # Trend chart (if date column available)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        trend_df = df.groupby('date').agg({'clicks': 'sum', 'impressions': 'sum'}).reset_index()
        st.markdown("### 📈 Performance Over Time")
        st.line_chart(trend_df.set_index('date'))

    # Top queries/pages by clicks
    st.markdown(f"### 🔝 Top {search_col.capitalize()}s by Clicks")
    st.dataframe(df.sort_values(by="clicks", ascending=False).head(10), use_container_width=True)

    # CTR vs Position plot
    st.markdown("### 📌 CTR vs Average Position")
    fig, ax = plt.subplots()
    ax.scatter(df["position"], df["ctr"], alpha=0.5, c='blue', edgecolors='w')
    ax.set_xlabel("Average Position")
    ax.set_ylabel("CTR (%)")
    ax.set_title("CTR vs Position")
    ax.invert_xaxis()
    plt.grid(True, linestyle="--", alpha=0.4)
    st.pyplot(fig)

    # Opportunity Keywords
    st.markdown("### 💡 Opportunity Keywords (Position 5–15, CTR < 5%)")
    opportunities = df[(df["position"] >= 5) & (df["position"] <= 15) & (df["ctr"] < 5)]
    st.dataframe(opportunities.sort_values(by="impressions", ascending=False).head(10), use_container_width=True)

    # Download opportunity keywords
    st.download_button(
        label="📥 Download Opportunities as CSV",
        data=opportunities.to_csv(index=False),
        file_name="opportunity_keywords.csv",
        mime="text/csv"
    )

else:
    st.info("📌 Please upload a CSV file exported from Google Search Console (Performance > Queries or Pages).")
