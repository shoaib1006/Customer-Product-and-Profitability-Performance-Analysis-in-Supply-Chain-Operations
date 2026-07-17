# Customer-Product-and-Profitability-Performance-Analysis-in-Supply-Chain-Operations

This project delivers a Streamlit analytics dashboard for APL Logistics to identify which customers, products, categories, markets, and regions generate real profit after discount impact.

## Implemented analysis scope

- Data cleaning and financial validation for revenue/profit/discount fields
- Revenue and profit KPI overview with profit margin and discount impact ratio
- Customer value diagnostics (top/bottom customers, segment contribution)
- Product and category profitability analysis (high revenue vs low margin visibility)
- Discount impact diagnostics (discount rate vs margin + what-if scenario)
- Market and regional profitability comparison

## Dashboard modules

- **Revenue & Profit Overview**
- **Customer Value Dashboard**
- **Product & Category Performance**
- **Discount Impact Analyzer**

## Local setup

```bash
pip install -r requirements.txt
```

## Run tests

```bash
python -m pytest -q
```

## Run dashboard

```bash
streamlit run app.py
```

## Data input

Upload a CSV containing the fields listed in the project problem statement, including:

- `Sales`, `Order Profit Per Order`, `Order Item Discount`, `Order Item Discount Rate`
- `Order Item Product Price`, `Order Item Quantity`, `Order Item Total`
- `Customer Id`, `Customer Segment`, `Category Name`, `Product Name`
- `Market`, `Order Region`, `Order Country`
