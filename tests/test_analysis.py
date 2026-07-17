import pandas as pd

from src.analysis import clean_and_validate, compute_kpis, simulate_discount_scenario


def test_clean_and_validate_filters_invalid_rows_and_computes_margin():
    df = pd.DataFrame(
        {
            "Sales": [100, 0, 200],
            "Order Profit Per Order": [20, 2, 10],
            "Order Item Discount": [5, 0, 20],
            "Order Item Discount Rate": [0.05, 0.0, 0.2],
            "Order Item Product Price": [50, 50, 100],
            "Order Item Quantity": [2, 0, 2],
            "Order Item Total": [95, 50, 180],
            "Customer Id": [1, 2, 3],
            "Category Name": ["A", "B", "A"],
            "Product Name": ["P1", "P2", "P3"],
            "Customer Segment": ["Consumer", "Corporate", "Consumer"],
            "Market": ["APAC", "EU", "APAC"],
            "Order Region": ["East", "West", "East"],
            "Order Country": ["IN", "FR", "IN"],
        }
    )

    out = clean_and_validate(df)

    assert len(out) == 2
    assert round(out["Profit Margin (%)"].iloc[0], 2) == 20.00
    assert "Discount Band" in out.columns


def test_compute_kpis_and_discount_scenario():
    df = pd.DataFrame(
        {
            "Sales": [100, 200],
            "Profit": [20, 30],
            "Discount Impact Amount": [5, 10],
        }
    )

    kpis = compute_kpis(df)
    assert kpis["Total Revenue"] == 300
    assert kpis["Total Profit"] == 50
    assert round(kpis["Profit Margin (%)"], 2) == 16.67
    assert round(kpis["Discount Impact Ratio (%)"], 2) == 5.00

    scenario = simulate_discount_scenario(df, 0.1)
    assert scenario["Baseline Profit"] == 50
    assert scenario["Projected Profit"] == 20
    assert scenario["Projected Profit Change"] == -30
