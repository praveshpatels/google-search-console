# -*- coding: utf-8 -*-
"""
Google Search Console Data Analyzer (Final Version with Plotly & Trendline)
Developed by Pravesh Patel
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

# Page setup
st.set_page_config(page_title="GSC Data Analyzer", page_icon="🔍", layout="wide")
st.title("🔍 Google Search Console Data Analyzer")
st.markdown("*Developed by **Pravesh Patel***", unsafe_allow_html=True)

# Upload file
uploaded_file = st.file_uploader("📁 Upload GSC CSV file (Performance > Queries)", type=["csv"])

if uploaded_file:
    # Read the CSV content
    raw_data = uploaded_file.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw_data))

    # Normalize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df.rename(columns={"top_queries": "query"}, inplace=True)

    # Check required columns
    required_cols = ["query", "clicks", "impressions", "ctr", "position"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"❌ Missing columns: {', '.join(missing)}")
        st.stop()

    # Clean numeric columns
    for col in ["clicks", "impressions", "position"]:
        df[col] = df[col].astype(str).str.replace(",", "", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["ctr"] = df["ctr"].astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False)
    df["ctr"] = pd.to_numeric(df["ctr"], errors="coerce")

    df.dropna(subset=["clicks", "impressions", "ctr", "position"], how="all", inplace=True)

    # Optional filtering
    with st.expander("🔍 Filter Data"):
        min_impr = st.slider("Minimum Impressions", 0, int(df["impressions"].max()), 100)
        keyword_filter = st.text_input("Filter by Query (Optional)", "")
        df = df[df["impressions"] >= min_impr]
        if keyword_filter:
            df = df[df["query"].str.contains(keyword_filter, case=False, na=False)]

    # Show raw data
    if st.checkbox("📄 Show Raw Data"):
        st.dataframe(df.head(25), use_container_width=True)

    # ✅ Weighted average metrics
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

    # Top Queries
    st.markdown("### 🔝 Top Queries by Clicks")
    st.dataframe(
        df.sort_values(by="clicks", ascending=False)[["query", "clicks", "impressions", "ctr", "position"]].head(10),
        use_container_width=True
    )

    # CTR vs Position Chart Explanation
    with st.expander("ℹ️ How to Read 'CTR vs Position' Chart"):
        st.markdown("""
        - **Each dot** = 1 keyword/query
        - **X-axis (Position):** Lower = higher Google ranking (1 = top)
        - **Y-axis (CTR):** Higher = better click-through rate

        ### Interpreting:
        - ✅ **Top-left:** Strong keywords (high CTR & top ranking)
        - ⚠️ **Bottom-left:** Good rank but low CTR → improve meta/title
        - 🚀 **Top-right:** Low rank but strong CTR → boost content/rank
        - ❌ **Bottom-right:** Poor rank & CTR → deprioritize
        """)

    # 📈 CTR vs Position using Plotly + trendline
    st.markdown("### 📌 CTR vs Average Position (Interactive Plotly)")
    df_sorted = df.sort_values("position")
    fig = px.scatter(
        df_sorted,
        x="position",
        y="ctr",
        hover_data=["query", "clicks", "impressions"],
        labels={"position": "Google Position", "ctr": "CTR (%)"},
        title="CTR vs Position",
        opacity=0.6
    )

    # Add trendline (linear regression)
    if len(df_sorted) > 1:
        z = np.polyfit(df_sorted["position"], df_sorted["ctr"], 1)
        p = np.poly1d(z)
        fig.add_trace(
            go.Scatter(
                x=df_sorted["position"],
                y=p(df_sorted["position"]),
                mode="lines",
                name="Trendline",
                line=dict(color="red", dash="dash")
            )
        )

    fig.update_layout(
        xaxis=dict(autorange="reversed"),  # Position 1 is best
        template="plotly_white",
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

    # Opportunity keywords
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

else:
    st.info("📌 Please upload a CSV file from Google Search Console > Performance > Queries tab.")
