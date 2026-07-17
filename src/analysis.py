from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "Sales",
    "Order Profit Per Order",
    "Order Item Discount",
    "Order Item Discount Rate",
    "Order Item Product Price",
    "Order Item Quantity",
    "Order Item Total",
    "Customer Id",
    "Category Name",
    "Product Name",
    "Customer Segment",
    "Market",
    "Order Region",
    "Order Country",
]


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce"
    )


def clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    out = df.copy()
    numeric_columns = [
        "Sales",
        "Order Profit Per Order",
        "Order Item Discount",
        "Order Item Discount Rate",
        "Order Item Product Price",
        "Order Item Quantity",
        "Order Item Total",
        "Order Item Profit Ratio",
        "Benefit per order",
    ]
    for col in numeric_columns:
        if col in out.columns:
            out[col] = _to_numeric(out[col])

    out["Sales"] = out["Sales"].fillna(0)
    out["Order Item Quantity"] = out["Order Item Quantity"].fillna(0)
    out = out[(out["Sales"] > 0) & (out["Order Item Quantity"] > 0)]

    out["Profit"] = out["Order Profit Per Order"].fillna(out.get("Benefit per order", 0))
    out["Profit Margin (%)"] = np.where(out["Sales"] > 0, (out["Profit"] / out["Sales"]) * 100, 0)
    out["Undiscounted Revenue"] = (
        out["Order Item Product Price"].fillna(0) * out["Order Item Quantity"].fillna(0)
    )
    out["Discount Impact Amount"] = (
        out["Undiscounted Revenue"] - out["Order Item Total"].fillna(out["Sales"])
    ).clip(lower=0)

    out["Order Item Discount Rate"] = out["Order Item Discount Rate"].fillna(0).clip(lower=0)
    out["Discount Band"] = pd.cut(
        out["Order Item Discount Rate"],
        bins=[-0.001, 0.05, 0.1, 0.2, 0.3, 1.0],
        labels=["0-5%", "5-10%", "10-20%", "20-30%", "30%+"],
    )

    return out.reset_index(drop=True)


def compute_kpis(df: pd.DataFrame) -> dict[str, float]:
    total_revenue = float(df["Sales"].sum())
    total_profit = float(df["Profit"].sum())
    margin = (total_profit / total_revenue * 100) if total_revenue else 0.0
    discount_impact_ratio = (
        (df["Discount Impact Amount"].sum() / total_revenue) * 100 if total_revenue else 0.0
    )
    return {
        "Total Revenue": total_revenue,
        "Total Profit": total_profit,
        "Profit Margin (%)": margin,
        "Discount Impact Ratio (%)": float(discount_impact_ratio),
    }


def aggregate_customer_value(df: pd.DataFrame) -> pd.DataFrame:
    customer_cols: Iterable[str] = ["Customer Id"]
    if "Customer Fname" in df.columns and "Customer Lname" in df.columns:
        customer_cols = ["Customer Id", "Customer Fname", "Customer Lname", "Customer Segment"]
    elif "Customer Segment" in df.columns:
        customer_cols = ["Customer Id", "Customer Segment"]

    out = (
        df.groupby(list(customer_cols), dropna=False)
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
            Customer_Value_Index=("Profit", "sum"),
        )
        .reset_index()
    )
    out["Profit Margin (%)"] = np.where(out["Sales"] > 0, (out["Profit"] / out["Sales"]) * 100, 0)
    return out.sort_values("Profit", ascending=False)


def aggregate_product_profitability(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby(["Category Name", "Product Name"], dropna=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .reset_index()
    )
    out["Profit Margin (%)"] = np.where(out["Sales"] > 0, (out["Profit"] / out["Sales"]) * 100, 0)
    return out.sort_values("Profit", ascending=False)


def aggregate_market_profitability(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby(["Market", "Order Region", "Order Country"], dropna=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .reset_index()
    )
    out["Profit Margin (%)"] = np.where(out["Sales"] > 0, (out["Profit"] / out["Sales"]) * 100, 0)
    return out.sort_values("Profit", ascending=False)


def discount_margin_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("Discount Band", dropna=False)
        .agg(
            Avg_Discount_Rate=("Order Item Discount Rate", "mean"),
            Avg_Margin=("Profit Margin (%)", "mean"),
            Total_Profit=("Profit", "sum"),
            Total_Sales=("Sales", "sum"),
        )
        .reset_index()
    )
    return out


def simulate_discount_scenario(df: pd.DataFrame, additional_discount_rate: float) -> dict[str, float]:
    baseline_profit = float(df["Profit"].sum())
    projected_profit = float((df["Profit"] - (df["Sales"] * additional_discount_rate)).sum())
    return {
        "Baseline Profit": baseline_profit,
        "Projected Profit": projected_profit,
        "Projected Profit Change": projected_profit - baseline_profit,
    }
