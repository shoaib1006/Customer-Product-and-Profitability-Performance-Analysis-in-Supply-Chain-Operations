from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analysis import (
    aggregate_customer_value,
    aggregate_market_profitability,
    aggregate_product_profitability,
    clean_and_validate,
    compute_kpis,
    discount_margin_diagnostics,
    simulate_discount_scenario,
)

st.set_page_config(page_title="APL Logistics Profitability Intelligence", layout="wide")
st.title("Customer, Product, and Profitability Performance Analysis")

uploaded_file = st.file_uploader("Upload order dataset (CSV)", type=["csv"])
if not uploaded_file:
    st.info("Upload a CSV file with the project columns to start the dashboard.")
    st.stop()

raw_df = pd.read_csv(uploaded_file)

try:
    df = clean_and_validate(raw_df)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

segment_options = sorted(df["Customer Segment"].dropna().unique().tolist())
category_options = sorted(df["Category Name"].dropna().unique().tolist())
market_options = sorted(df["Market"].dropna().unique().tolist())
region_options = sorted(df["Order Region"].dropna().unique().tolist())

with st.sidebar:
    st.header("Filters")
    selected_segments = st.multiselect("Customer Segment", segment_options, default=segment_options)
    selected_categories = st.multiselect("Category", category_options, default=category_options)
    selected_market = st.selectbox("Market", ["All"] + market_options)
    selected_region = st.selectbox("Order Region", ["All"] + region_options)
    scenario_discount = st.slider("What-if extra discount rate", min_value=0.0, max_value=0.3, value=0.0, step=0.01)

filtered = df[
    df["Customer Segment"].isin(selected_segments) & df["Category Name"].isin(selected_categories)
]
if selected_market != "All":
    filtered = filtered[filtered["Market"] == selected_market]
if selected_region != "All":
    filtered = filtered[filtered["Order Region"] == selected_region]

if filtered.empty:
    st.warning("No data after applying selected filters.")
    st.stop()

kpis = compute_kpis(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${kpis['Total Revenue']:,.2f}")
col2.metric("Total Profit", f"${kpis['Total Profit']:,.2f}")
col3.metric("Profit Margin", f"{kpis['Profit Margin (%)']:.2f}%")
col4.metric("Discount Impact Ratio", f"{kpis['Discount Impact Ratio (%)']:.2f}%")

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Revenue & Profit Overview",
        "Customer Value Dashboard",
        "Product & Category Performance",
        "Discount Impact Analyzer",
    ]
)

with tab1:
    market_df = aggregate_market_profitability(filtered)
    st.subheader("Market and Regional Profitability")
    st.dataframe(market_df, use_container_width=True)
    fig = px.bar(
        market_df,
        x="Order Region",
        y="Profit",
        color="Market",
        hover_data=["Sales", "Profit Margin (%)"],
        title="Profit by Region and Market",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    customer_df = aggregate_customer_value(filtered)
    st.subheader("Top and Bottom Customers by Profit")
    c1, c2 = st.columns(2)
    c1.dataframe(customer_df.head(10), use_container_width=True)
    c2.dataframe(customer_df.tail(10), use_container_width=True)

    segment_contribution = customer_df.groupby("Customer Segment", dropna=False)["Profit"].sum().reset_index()
    seg_fig = px.pie(segment_contribution, names="Customer Segment", values="Profit", title="Customer Segment Contribution")
    st.plotly_chart(seg_fig, use_container_width=True)

with tab3:
    product_df = aggregate_product_profitability(filtered)
    st.subheader("Product-Level Margin Analysis")
    st.dataframe(product_df.head(25), use_container_width=True)

    category_heat = product_df.groupby("Category Name", dropna=False).agg(
        Profit=("Profit", "sum"),
        Sales=("Sales", "sum"),
    ).reset_index()
    category_heat["Margin"] = category_heat["Profit"] / category_heat["Sales"].where(category_heat["Sales"] != 0, 1)
    heat_fig = px.density_heatmap(
        category_heat,
        x="Category Name",
        y="Margin",
        z="Profit",
        color_continuous_scale="RdYlGn",
        title="Category Profitability Heatmap",
    )
    st.plotly_chart(heat_fig, use_container_width=True)

with tab4:
    diagnostics = discount_margin_diagnostics(filtered)
    st.subheader("Discount vs Margin")
    diag_fig = px.scatter(
        filtered,
        x="Order Item Discount Rate",
        y="Profit Margin (%)",
        color="Category Name",
        title="Discount Rate vs Profit Margin",
        opacity=0.6,
    )
    st.plotly_chart(diag_fig, use_container_width=True)
    st.dataframe(diagnostics, use_container_width=True)

    scenario = simulate_discount_scenario(filtered, scenario_discount)
    s1, s2, s3 = st.columns(3)
    s1.metric("Baseline Profit", f"${scenario['Baseline Profit']:,.2f}")
    s2.metric("Projected Profit", f"${scenario['Projected Profit']:,.2f}")
    s3.metric("Projected Profit Change", f"${scenario['Projected Profit Change']:,.2f}")
