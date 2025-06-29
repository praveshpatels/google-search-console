# -*- coding: utf-8 -*-

"""
Google Search Console Data Analyzer
Developed by Pravesh Patel
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="GSC Analyzer", layout="wide")

st.title("Google Search Console Data Analyzer")
st.markdown("*Developed by **Pravesh Patel***", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload GSC CSV Export (Performance > Queries or Pages)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Preprocessing
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]

    # Clean numeric columns
    for col in ["clicks", "impressions", "ctr", "position"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Show raw data toggle
    if st.checkbox("Show Raw Data"):
        st.dataframe(df.head())

    # KPIs
    total_clicks = df["clicks"].sum()
    total_impressions = df["impressions"].sum()
    avg_ctr = df["ctr"].mean() * 100
    avg_position = df["position"].mean()

    st.markdown("### Overall Performance")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Clicks", f"{total_clicks:,}")
    col2.metric("Total Impressions", f"{total_impressions:,}")
    col3.metric("Avg. CTR", f"{avg_ctr:.2f}%")
    col4.metric("Avg. Position", f"{avg_position:.2f}")

    # Top Queries
    st.markdown("### Top Queries by Clicks")
    st.dataframe(df.sort_values(by="clicks", ascending=False).head(10))

    # CTR vs Position Scatter Plot
    st.markdown("### CTR vs Position")
    fig, ax = plt.subplots()
    ax.scatter(df["position"], df["ctr"] * 100, alpha=0.5)
    ax.set_xlabel("Average Position")
    ax.set_ylabel("CTR (%)")
    ax.set_title("CTR vs Position")
    st.pyplot(fig)

    # Opportunity Queries: Good Position, Low CTR
    st.markdown("### Opportunity Keywords (Position 5–15, Low CTR)")
    opportunities = df[(df["position"] >= 5) & (df["position"] <= 15) & (df["ctr"] < 0.05)]
    st.dataframe(opportunities.sort_values(by="impressions", ascending=False).head(10))

    # Download Opportunity CSV
    st.download_button(
        label="Download Opportunities as CSV",
        data=opportunities.to_csv(index=False),
        file_name="opportunity_keywords.csv",
        mime="text/csv"
    )

else:
    st.info("Please upload a CSV file exported from Google Search Console (Performance > Queries or Pages).")
