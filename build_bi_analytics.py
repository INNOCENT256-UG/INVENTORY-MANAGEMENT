"""
Enterprise CRM, Sales & Inventory Business Intelligence ETL Pipeline
====================================================================
Processes raw CSV datasets into an enriched analytical data model for:
1. Interactive D3.js Executive & Operational BI Dashboard (index.html / dashboard_data.js)
2. High-resolution static SVG chart previews in Charts/ for GitHub README portfolio showcase
"""

import json
import os
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "CSV FILES-RAW_DATA"
CHARTS_DIR = BASE_DIR / "Charts"
CHARTS_DIR.mkdir(exist_ok=True)


def load_datasets():
    inv_retail = pd.read_csv(RAW_DIR / "inventory_data.csv")
    customers = pd.read_csv(RAW_DIR / "customers.csv")
    transactions = pd.read_csv(RAW_DIR / "sales_transactions.csv")
    crm_products = pd.read_csv(RAW_DIR / "product_inventory.csv")
    pipeline = pd.read_csv(RAW_DIR / "sales_pipeline.csv")
    return inv_retail, customers, transactions, crm_products, pipeline


def enrich_inventory(inv: pd.DataFrame) -> pd.DataFrame:
    df = inv.copy()
    df["Stock Value"] = (df["Quantity In Stock"] * df["Unit Cost"]).round(2)
    df["Retail Value"] = (df["Quantity In Stock"] * df["Selling Price"]).round(2)
    df["Profit Margin %"] = np.where(
        df["Revenue"] > 0, (df["Profit"] / df["Revenue"] * 100).round(2), 0.0
    )
    df["Stock Ratio"] = np.where(
        df["Reorder Level"] > 0,
        (df["Quantity In Stock"] / df["Reorder Level"]).round(2),
        1.0,
    )

    # Stock Health Status
    conditions = [
        df["Quantity In Stock"] == 0,
        df["Quantity In Stock"] <= (df["Reorder Level"] * 0.5),
        df["Quantity In Stock"] < df["Reorder Level"],
        df["Quantity In Stock"] > (df["Reorder Level"] * 4.0),
    ]
    choices = ["Out of Stock", "Critical Low", "Below Reorder", "Overstocked"]
    df["Stock Status"] = np.select(conditions, choices, default="Optimal")

    # ABC Pareto Classification by Revenue
    df = df.sort_values("Revenue", ascending=False).reset_index(drop=True)
    cum_rev = df["Revenue"].cumsum() / df["Revenue"].sum()
    df["ABC Class"] = np.select(
        [cum_rev <= 0.70, cum_rev <= 0.90],
        ["A (Top 70% Rev)", "B (Next 20% Rev)"],
        default="C (Bottom 10% Rev)",
    )
    return df


def build_analytics_payload():
    inv_raw, customers, tx, crm_prod, pipeline = load_datasets()
    inv = enrich_inventory(inv_raw)

    # --- 1. Executive KPIs (Inventory Dataset + CRM Sales Dataset) ---
    inv_kpis = {
        "total_skus": int(len(inv)),
        "total_inventory_cost_value": round(float(inv["Stock Value"].sum()), 2),
        "total_inventory_retail_value": round(float(inv["Retail Value"].sum()), 2),
        "total_revenue": round(float(inv["Revenue"].sum()), 2),
        "total_profit": round(float(inv["Profit"].sum()), 2),
        "avg_profit_margin": round(
            float(inv["Profit"].sum() / inv["Revenue"].sum() * 100), 2
        ),
        "total_units_in_stock": int(inv["Quantity In Stock"].sum()),
        "total_units_sold": int(inv["Sales Quantity"].sum()),
        "low_stock_skus": int((inv["Quantity In Stock"] < inv["Reorder Level"]).sum()),
        "critical_low_skus": int(
            (inv["Stock Status"].isin(["Out of Stock", "Critical Low"])).sum()
        ),
        "out_of_stock_skus": int((inv["Quantity In Stock"] == 0).sum()),
        "overstocked_skus": int((inv["Stock Status"] == "Overstocked").sum()),
        "inventory_turnover": round(
            float(inv["Sales Quantity"].sum() / max(inv["Quantity In Stock"].mean(), 1)),
            2,
        ),
    }

    # --- 2. Category Breakdown ---
    cat_grp = (
        inv.groupby("Category", as_index=False)
        .agg(
            skus=("Product ID", "count"),
            revenue=("Revenue", "sum"),
            profit=("Profit", "sum"),
            stock_value=("Stock Value", "sum"),
            units_in_stock=("Quantity In Stock", "sum"),
            units_sold=("Sales Quantity", "sum"),
            low_stock_count=(
                "Quantity In Stock",
                lambda s: int((s < inv.loc[s.index, "Reorder Level"]).sum()),
            ),
        )
        .sort_values("revenue", ascending=False)
    )
    cat_grp["margin_pct"] = (cat_grp["profit"] / cat_grp["revenue"] * 100).round(2)
    cat_grp["revenue_share_pct"] = (
        cat_grp["revenue"] / cat_grp["revenue"].sum() * 100
    ).round(2)
    cat_grp["revenue"] = cat_grp["revenue"].round(2)
    cat_grp["profit"] = cat_grp["profit"].round(2)
    cat_grp["stock_value"] = cat_grp["stock_value"].round(2)

    # --- 3. Warehouse & Category Heatmap Matrix ---
    wh_cat = (
        inv.groupby(["Warehouse Location", "Category"], as_index=False)
        .agg(
            stock_value=("Stock Value", "sum"),
            revenue=("Revenue", "sum"),
            units_in_stock=("Quantity In Stock", "sum"),
            low_stock=("Stock Status", lambda s: int(s.isin(["Out of Stock", "Critical Low", "Below Reorder"]).sum())),
            skus=("Product ID", "count"),
        )
    )
    wh_cat["stock_value"] = wh_cat["stock_value"].round(2)
    wh_cat["revenue"] = wh_cat["revenue"].round(2)

    # Warehouse summary
    wh_grp = (
        inv.groupby("Warehouse Location", as_index=False)
        .agg(
            skus=("Product ID", "count"),
            stock_value=("Stock Value", "sum"),
            revenue=("Revenue", "sum"),
            profit=("Profit", "sum"),
            units_in_stock=("Quantity In Stock", "sum"),
            low_stock=("Stock Status", lambda s: int(s.isin(["Out of Stock", "Critical Low", "Below Reorder"]).sum())),
        )
        .sort_values("stock_value", ascending=False)
    )
    wh_grp["stock_value"] = wh_grp["stock_value"].round(2)
    wh_grp["revenue"] = wh_grp["revenue"].round(2)
    wh_grp["profit"] = wh_grp["profit"].round(2)

    # --- 4. Supplier Performance ---
    sup_grp = (
        inv.groupby("Supplier", as_index=False)
        .agg(
            skus=("Product ID", "count"),
            revenue=("Revenue", "sum"),
            profit=("Profit", "sum"),
            stock_value=("Stock Value", "sum"),
            units_sold=("Sales Quantity", "sum"),
            low_stock_skus=("Stock Status", lambda s: int(s.isin(["Out of Stock", "Critical Low", "Below Reorder"]).sum())),
        )
        .sort_values("revenue", ascending=False)
    )
    sup_grp["margin_pct"] = (sup_grp["profit"] / sup_grp["revenue"] * 100).round(2)
    sup_grp["risk_rate_pct"] = (sup_grp["low_stock_skus"] / sup_grp["skus"] * 100).round(1)
    sup_grp["revenue"] = sup_grp["revenue"].round(2)
    sup_grp["profit"] = sup_grp["profit"].round(2)
    sup_grp["stock_value"] = sup_grp["stock_value"].round(2)

    # --- 5. Stock Status & ABC Distribution (for Interactive Donut/Pie Charts) ---
    status_grp = (
        inv.groupby("Stock Status", as_index=False)
        .agg(
            skus=("Product ID", "count"),
            stock_value=("Stock Value", "sum"),
            revenue_at_risk=("Revenue", "sum"),
        )
    )
    status_grp["stock_value"] = status_grp["stock_value"].round(2)
    status_grp["revenue_at_risk"] = status_grp["revenue_at_risk"].round(2)

    abc_grp = (
        inv.groupby("ABC Class", as_index=False)
        .agg(
            skus=("Product ID", "count"),
            revenue=("Revenue", "sum"),
            profit=("Profit", "sum"),
            stock_value=("Stock Value", "sum"),
        )
        .sort_values("ABC Class")
    )
    abc_grp["revenue"] = abc_grp["revenue"].round(2)
    abc_grp["profit"] = abc_grp["profit"].round(2)
    abc_grp["stock_value"] = abc_grp["stock_value"].round(2)

    # --- 6. Monthly Purchase & Revenue Trend (Inventory Dataset) ---
    inv["Purchase Month"] = pd.to_datetime(inv["Purchase Date"]).dt.to_period("M").astype(str)
    inv_monthly = (
        inv.groupby("Purchase Month", as_index=False)
        .agg(
            revenue=("Revenue", "sum"),
            profit=("Profit", "sum"),
            stock_value=("Stock Value", "sum"),
            units_sold=("Sales Quantity", "sum"),
            skus_restocked=("Product ID", "count"),
        )
        .sort_values("Purchase Month")
    )
    inv_monthly["revenue"] = inv_monthly["revenue"].round(2)
    inv_monthly["profit"] = inv_monthly["profit"].round(2)
    inv_monthly["stock_value"] = inv_monthly["stock_value"].round(2)

    # --- 7. Top SKUs & Critical Reorder Alerts ---
    top_skus = (
        inv.sort_values("Revenue", ascending=False)
        .head(20)[
            [
                "Product ID",
                "Product Name",
                "Category",
                "Supplier",
                "Warehouse Location",
                "Unit Cost",
                "Selling Price",
                "Quantity In Stock",
                "Reorder Level",
                "Sales Quantity",
                "Revenue",
                "Profit",
                "Profit Margin %",
                "Stock Status",
                "ABC Class",
            ]
        ]
        .to_dict(orient="records")
    )

    reorder_alerts = (
        inv[inv["Quantity In Stock"] < inv["Reorder Level"]]
        .assign(
            deficit=lambda d: d["Reorder Level"] - d["Quantity In Stock"],
            reorder_cost=lambda d: (
                (d["Reorder Level"] * 2 - d["Quantity In Stock"]) * d["Unit Cost"]
            ).round(2),
        )
        .sort_values(["Quantity In Stock", "Revenue"], ascending=[True, False])
        .head(30)[
            [
                "Product ID",
                "Product Name",
                "Category",
                "Supplier",
                "Warehouse Location",
                "Quantity In Stock",
                "Reorder Level",
                "deficit",
                "Unit Cost",
                "reorder_cost",
                "Revenue",
                "Profit Margin %",
                "Stock Status",
                "ABC Class",
            ]
        ]
        .to_dict(orient="records")
    )

    # --- 8. CRM & Sales Pipeline Analytics ---
    tx_merged = tx.merge(customers, on="Customer ID", how="left").merge(
        crm_prod[["Product ID", "Product Name", "Category", "Supplier"]],
        on="Product ID",
        how="left",
    )
    tx_merged["Order Month"] = (
        pd.to_datetime(tx_merged["Order Date"]).dt.to_period("M").astype(str)
    )

    crm_kpis = {
        "total_customers": int(len(customers)),
        "active_customers": int((customers["Customer Status"] == "Active").sum()),
        "churned_customers": int((customers["Customer Status"] == "Churned").sum()),
        "total_orders": int(len(tx)),
        "completed_orders": int((tx["Sales Status"] == "Completed").sum()),
        "tx_total_revenue": round(float(tx["Revenue"].sum()), 2),
        "tx_completed_revenue": round(
            float(tx.loc[tx["Sales Status"] == "Completed", "Revenue"].sum()), 2
        ),
        "tx_total_profit": round(float(tx["Profit"].sum()), 2),
        "avg_order_value": round(float(tx["Revenue"].mean()), 2),
        "pipeline_total_leads": int(len(pipeline)),
        "pipeline_total_opportunity": round(
            float(pipeline["Opportunity Value"].sum()), 2
        ),
        "pipeline_expected_revenue": round(
            float(pipeline["Expected Revenue"].sum()), 2
        ),
        "pipeline_win_rate_pct": round(
            float(
                (pipeline["Sales Stage"] == "Closed Won").sum()
                / max(
                    (
                        pipeline["Sales Stage"].isin(["Closed Won", "Closed Lost"])
                    ).sum(),
                    1,
                )
                * 100
            ),
            1,
        ),
    }

    crm_monthly = (
        tx_merged.groupby("Order Month", as_index=False)
        .agg(
            revenue=("Revenue", "sum"),
            profit=("Profit", "sum"),
            orders=("Order ID", "count"),
            units=("Quantity Sold", "sum"),
        )
        .sort_values("Order Month")
    )
    crm_monthly["revenue"] = crm_monthly["revenue"].round(2)
    crm_monthly["profit"] = crm_monthly["profit"].round(2)

    rep_perf = (
        tx_merged.groupby("Sales Representative", as_index=False)
        .agg(
            orders=("Order ID", "count"),
            revenue=("Revenue", "sum"),
            profit=("Profit", "sum"),
            avg_discount=("Discount", lambda s: round(float(s.mean() * 100), 1)),
            completed_orders=(
                "Sales Status",
                lambda s: int((s == "Completed").sum()),
            ),
        )
        .sort_values("revenue", ascending=False)
    )
    rep_perf["margin_pct"] = (rep_perf["profit"] / rep_perf["revenue"] * 100).round(2)
    rep_perf["revenue"] = rep_perf["revenue"].round(2)
    rep_perf["profit"] = rep_perf["profit"].round(2)

    seg_perf = (
        tx_merged.groupby("Customer Segment", as_index=False)
        .agg(
            revenue=("Revenue", "sum"),
            profit=("Profit", "sum"),
            orders=("Order ID", "count"),
            customers=("Customer ID", "nunique"),
        )
        .sort_values("revenue", ascending=False)
    )
    seg_perf["revenue"] = seg_perf["revenue"].round(2)
    seg_perf["profit"] = seg_perf["profit"].round(2)

    ind_perf = (
        tx_merged.groupby("Industry", as_index=False)
        .agg(
            revenue=("Revenue", "sum"),
            profit=("Profit", "sum"),
            orders=("Order ID", "count"),
            customers=("Customer ID", "nunique"),
        )
        .sort_values("revenue", ascending=False)
    )
    ind_perf["revenue"] = ind_perf["revenue"].round(2)
    ind_perf["profit"] = ind_perf["profit"].round(2)

    stage_order = [
        "Prospecting",
        "Qualification",
        "Proposal",
        "Negotiation",
        "Closed Won",
        "Closed Lost",
    ]
    pipeline_stages = (
        pipeline.groupby("Sales Stage", as_index=False)
        .agg(
            leads=("Lead ID", "count"),
            opportunity_value=("Opportunity Value", "sum"),
            expected_revenue=("Expected Revenue", "sum"),
        )
    )
    pipeline_stages["order"] = pipeline_stages["Sales Stage"].apply(
        lambda x: stage_order.index(x) if x in stage_order else 99
    )
    pipeline_stages = pipeline_stages.sort_values("order").drop(columns=["order"])
    pipeline_stages["opportunity_value"] = pipeline_stages["opportunity_value"].round(2)
    pipeline_stages["expected_revenue"] = pipeline_stages["expected_revenue"].round(2)

    # All 1,188 SKUs compact list for interactive cross-filtering in D3
    sku_records = (
        inv[
            [
                "Product ID",
                "Product Name",
                "Category",
                "Supplier",
                "Purchase Month",
                "Unit Cost",
                "Selling Price",
                "Quantity In Stock",
                "Reorder Level",
                "Warehouse Location",
                "Sales Quantity",
                "Revenue",
                "Profit",
                "Stock Value",
                "Profit Margin %",
                "Stock Status",
                "ABC Class",
            ]
        ]
        .rename(
            columns={
                "Product ID": "id",
                "Product Name": "name",
                "Category": "category",
                "Supplier": "supplier",
                "Purchase Month": "month",
                "Unit Cost": "cost",
                "Selling Price": "price",
                "Quantity In Stock": "stock",
                "Reorder Level": "reorder",
                "Warehouse Location": "warehouse",
                "Sales Quantity": "sold",
                "Revenue": "revenue",
                "Profit": "profit",
                "Stock Value": "stock_value",
                "Profit Margin %": "margin",
                "Stock Status": "status",
                "ABC Class": "abc",
            }
        )
        .to_dict(orient="records")
    )

    payload = {
        "generated_at": "2026-11-23",
        "inventory_kpis": inv_kpis,
        "crm_kpis": crm_kpis,
        "categories": cat_grp.to_dict(orient="records"),
        "warehouses": wh_grp.to_dict(orient="records"),
        "warehouse_category_matrix": wh_cat.to_dict(orient="records"),
        "suppliers": sup_grp.to_dict(orient="records"),
        "stock_status_distribution": status_grp.to_dict(orient="records"),
        "abc_distribution": abc_grp.to_dict(orient="records"),
        "inventory_monthly_trend": inv_monthly.to_dict(orient="records"),
        "top_skus": top_skus,
        "reorder_alerts": reorder_alerts,
        "crm_monthly_trend": crm_monthly.to_dict(orient="records"),
        "sales_reps": rep_perf.to_dict(orient="records"),
        "customer_segments": seg_perf.to_dict(orient="records"),
        "industries": ind_perf.to_dict(orient="records"),
        "pipeline_stages": pipeline_stages.to_dict(orient="records"),
        "skus": sku_records,
    }
    return payload


def generate_svg_chart_previews(data: dict):
    """Generates crisp, recruiter-ready SVG visual previews in Charts/ for GitHub README."""
    cats = data["categories"]
    kpis = data["inventory_kpis"]
    crm = data["crm_kpis"]
    whs = data["warehouses"]
    status_dist = data["stock_status_distribution"]
    abc_dist = data["abc_distribution"]
    reps = data["sales_reps"]
    stages = data["pipeline_stages"]

    # 1. Executive BI Dashboard Preview SVG
    svg_exec = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 680" width="100%" height="100%" font-family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0b0f19"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
    <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#3b82f6"/>
      <stop offset="100%" stop-color="#06b6d4"/>
    </linearGradient>
    <linearGradient id="profitGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#34d399"/>
    </linearGradient>
    <linearGradient id="accentCard" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>

  <rect width="1200" height="680" rx="16" fill="url(#bgGrad)"/>

  <!-- Header -->
  <rect x="24" y="20" width="1152" height="68" rx="12" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <circle cx="52" cy="54" r="12" fill="#3b82f6"/>
  <path d="M47 58 L52 48 L57 58 Z" fill="#fff"/>
  <text x="76" y="49" fill="#f8fafc" font-size="20" font-weight="700">ENTERPRISE SUPPLY CHAIN &amp; REVENUE BI COMMAND CENTER</text>
  <text x="76" y="70" fill="#94a3b8" font-size="12">Interactive D3.js Analytics Suite • 1,188 Active SKUs • 8 Warehouses • 1,000 CRM Transactions</text>
  <rect x="1020" y="37" width="136" height="34" rx="17" fill="#065f46" stroke="#10b981" stroke-width="1"/>
  <circle cx="1040" cy="54" r="5" fill="#34d399"/>
  <text x="1054" y="58" fill="#ecfdf5" font-size="12" font-weight="600">D3.js v7 LIVE</text>

  <!-- 5 KPI Cards -->
  <!-- Card 1 -->
  <rect x="24" y="104" width="218" height="102" rx="12" fill="url(#accentCard)" stroke="#334155"/>
  <text x="42" y="130" fill="#94a3b8" font-size="12" font-weight="600">TOTAL RETAIL REVENUE</text>
  <text x="42" y="166" fill="#f8fafc" font-size="28" font-weight="800">${kpis['total_revenue']/1e6:.2f}M</text>
  <text x="42" y="190" fill="#34d399" font-size="12" font-weight="600">▲ ${kpis['total_revenue']:,.0f} across 8 categories</text>

  <!-- Card 2 -->
  <rect x="257" y="104" width="218" height="102" rx="12" fill="url(#accentCard)" stroke="#334155"/>
  <text x="275" y="130" fill="#94a3b8" font-size="12" font-weight="600">NET GROSS PROFIT</text>
  <text x="275" y="166" fill="#10b981" font-size="28" font-weight="800">${kpis['total_profit']/1e6:.2f}M</text>
  <text x="275" y="190" fill="#34d399" font-size="12" font-weight="600">▲ {kpis['avg_profit_margin']}% Gross Margin Ratio</text>

  <!-- Card 3 -->
  <rect x="490" y="104" width="218" height="102" rx="12" fill="url(#accentCard)" stroke="#334155"/>
  <text x="508" y="130" fill="#94a3b8" font-size="12" font-weight="600">INVENTORY ASSET VALUE</text>
  <text x="508" y="166" fill="#38bdf8" font-size="28" font-weight="800">${kpis['total_inventory_cost_value']/1e6:.2f}M</text>
  <text x="508" y="190" fill="#94a3b8" font-size="12" font-weight="500">{kpis['total_units_in_stock']:,} units ({kpis['total_skus']:,} SKUs)</text>

  <!-- Card 4 -->
  <rect x="723" y="104" width="218" height="102" rx="12" fill="url(#accentCard)" stroke="#334155"/>
  <text x="741" y="130" fill="#94a3b8" font-size="12" font-weight="600">REORDER RISK ALERTS</text>
  <text x="741" y="166" fill="#f59e0b" font-size="28" font-weight="800">{kpis['low_stock_skus']} SKUs</text>
  <text x="741" y="190" fill="#f87171" font-size="12" font-weight="600">⚠ {kpis['critical_low_skus']} Critical / {kpis['out_of_stock_skus']} Out of Stock</text>

  <!-- Card 5 -->
  <rect x="956" y="104" width="220" height="102" rx="12" fill="url(#accentCard)" stroke="#334155"/>
  <text x="974" y="130" fill="#94a3b8" font-size="12" font-weight="600">CRM PIPELINE OPPORTUNITY</text>
  <text x="974" y="166" fill="#a855f7" font-size="28" font-weight="800">${crm['pipeline_total_opportunity']/1e6:.2f}M</text>
  <text x="974" y="190" fill="#c084fc" font-size="12" font-weight="600">${crm['pipeline_expected_revenue']/1e6:.2f}M Weighted • {crm['pipeline_win_rate_pct']}% Win Rate</text>

  <!-- Left Panel: Category Revenue & Profit Horizontal Multi-Bar Chart -->
  <rect x="24" y="222" width="710" height="434" rx="12" fill="#1e293b" stroke="#334155"/>
  <text x="48" y="254" fill="#f8fafc" font-size="16" font-weight="700">Category Revenue vs. Net Profit Performance</text>
  <text x="48" y="274" fill="#94a3b8" font-size="12">Ranked by revenue contribution with gross profit overlay &amp; margin %</text>
  <rect x="520" y="242" width="12" height="12" rx="3" fill="url(#barGrad)"/>
  <text x="538" y="253" fill="#cbd5e1" font-size="12">Revenue</text>
  <rect x="605" y="242" width="12" height="12" rx="3" fill="url(#profitGrad)"/>
  <text x="623" y="253" fill="#cbd5e1" font-size="12">Net Profit</text>
"""
    max_rev = max(c["revenue"] for c in cats)
    for i, c in enumerate(cats):
        y = 304 + i * 42
        rev_w = int((c["revenue"] / max_rev) * 380)
        prof_w = int((c["profit"] / max_rev) * 380)
        svg_exec += f"""
  <text x="48" y="{y+15}" fill="#e2e8f0" font-size="13" font-weight="600">{c['Category'].replace('&', '&amp;')}</text>
  <rect x="195" y="{y}" width="390" height="24" rx="6" fill="#0f172a"/>
  <rect x="195" y="{y}" width="{rev_w}" height="13" rx="4" fill="url(#barGrad)"/>
  <rect x="195" y="{y+13}" width="{prof_w}" height="11" rx="4" fill="url(#profitGrad)"/>
  <text x="598" y="{y+16}" fill="#f8fafc" font-size="12" font-weight="700">${c['revenue']/1e6:.2f}M</text>
  <text x="665" y="{y+16}" fill="#34d399" font-size="12" font-weight="600">({c['margin_pct']:.1f}%)</text>"""

    # Right Panel: Stock Health & ABC Pareto Breakdown
    svg_exec += """
  <rect x="750" y="222" width="426" height="210" rx="12" fill="#1e293b" stroke="#334155"/>
  <text x="774" y="254" fill="#f8fafc" font-size="16" font-weight="700">Stock Health &amp; Replenishment Risk</text>
  <text x="774" y="274" fill="#94a3b8" font-size="12">Distribution of 1,188 SKUs across operational risk tiers</text>
"""
    status_colors = {
        "Optimal": "#10b981",
        "Overstocked": "#3b82f6",
        "Below Reorder": "#f59e0b",
        "Critical Low": "#f97316",
        "Out of Stock": "#ef4444",
    }
    status_order = ["Optimal", "Overstocked", "Below Reorder", "Critical Low", "Out of Stock"]
    status_map = {s["Stock Status"]: s for s in status_dist}
    for idx, st in enumerate(status_order):
        s_obj = status_map.get(st, {"skus": 0, "stock_value": 0})
        y = 296 + idx * 25
        pct = s_obj["skus"] / max(kpis["total_skus"], 1) * 100
        bar_w = max(int(pct * 2.1), 4)
        col = status_colors[st]
        svg_exec += f"""
  <circle cx="782" cy="{y+7}" r="5" fill="{col}"/>
  <text x="796" y="{y+11}" fill="#e2e8f0" font-size="12" font-weight="600">{st}</text>
  <rect x="905" y="{y}" width="170" height="14" rx="4" fill="#0f172a"/>
  <rect x="905" y="{y}" width="{bar_w}" height="14" rx="4" fill="{col}"/>
  <text x="1085" y="{y+11}" fill="#f8fafc" font-size="12" font-weight="700">{s_obj['skus']} ({pct:.1f}%)</text>"""

    # Bottom Right Panel: ABC Pareto Revenue Concentration
    svg_exec += """
  <rect x="750" y="446" width="426" height="210" rx="12" fill="#1e293b" stroke="#334155"/>
  <text x="774" y="478" fill="#f8fafc" font-size="16" font-weight="700">ABC Pareto Inventory Classification</text>
  <text x="774" y="498" fill="#94a3b8" font-size="12">Capital &amp; revenue concentration across SKU tiers</text>
"""
    abc_colors = ["#38bdf8", "#a855f7", "#64748b"]
    for idx, a in enumerate(abc_dist):
        y = 524 + idx * 40
        col = abc_colors[idx % 3]
        rev_share = a["revenue"] / kpis["total_revenue"] * 100
        sku_share = a["skus"] / kpis["total_skus"] * 100
        svg_exec += f"""
  <rect x="774" y="{y}" width="378" height="32" rx="6" fill="#0f172a" stroke="#334155" stroke-width="0.8"/>
  <rect x="774" y="{y}" width="8" height="32" rx="4" fill="{col}"/>
  <text x="794" y="{y+20}" fill="#f8fafc" font-size="13" font-weight="700">{a['ABC Class']}</text>
  <text x="955" y="{y+20}" fill="#94a3b8" font-size="12">{a['skus']} SKUs ({sku_share:.0f}%)</text>
  <text x="1065" y="{y+20}" fill="{col}" font-size="13" font-weight="700">${a['revenue']/1e6:.2f}M ({rev_share:.0f}%)</text>"""

    svg_exec += "\n</svg>"
    (CHARTS_DIR / "executive_bi_overview.svg").write_text(svg_exec, encoding="utf-8")

    # 2. CRM Sales & Pipeline Funnel SVG Preview
    svg_crm = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 540" width="100%" height="100%" font-family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">
  <defs>
    <linearGradient id="bg2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0b0f19"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
    <linearGradient id="repBar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#6366f1"/>
      <stop offset="100%" stop-color="#a855f7"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="540" rx="16" fill="url(#bg2)"/>

  <!-- Left: Sales Rep Leaderboard -->
  <rect x="24" y="24" width="564" height="492" rx="12" fill="#1e293b" stroke="#334155"/>
  <text x="48" y="58" fill="#f8fafc" font-size="18" font-weight="700">Sales Representative Performance Leaderboard</text>
  <text x="48" y="78" fill="#94a3b8" font-size="12">1,000 CRM Transactions • Total Revenue ${crm['tx_total_revenue']:,.0f} • Profit ${crm['tx_total_profit']:,.0f}</text>
"""
    max_rep_rev = max(r["revenue"] for r in reps)
    for i, r in enumerate(reps):
        y = 108 + i * 54
        w = int((r["revenue"] / max_rep_rev) * 280)
        svg_crm += f"""
  <text x="48" y="{y+18}" fill="#f8fafc" font-size="13" font-weight="600">{i+1}. {r['Sales Representative']}</text>
  <text x="48" y="{y+36}" fill="#94a3b8" font-size="11">{r['orders']} Orders • Avg Discount {r['avg_discount']}%</text>
  <rect x="215" y="{y+8}" width="285" height="22" rx="6" fill="#0f172a"/>
  <rect x="215" y="{y+8}" width="{w}" height="22" rx="6" fill="url(#repBar)"/>
  <text x="510" y="{y+24}" fill="#e2e8f0" font-size="13" font-weight="700">${r['revenue']/1e3:.0f}K</text>"""

    # Right: Sales Pipeline Conversion Funnel & Warehouse Capital Allocation
    svg_crm += f"""
  <rect x="612" y="24" width="564" height="492" rx="12" fill="#1e293b" stroke="#334155"/>
  <text x="636" y="58" fill="#f8fafc" font-size="18" font-weight="700">CRM Deal Pipeline &amp; Expected Revenue Funnel</text>
  <text x="636" y="78" fill="#94a3b8" font-size="12">150 Active Deals • ${crm['pipeline_total_opportunity']/1e6:.2f}M Gross Pipeline • ${crm['pipeline_expected_revenue']/1e6:.2f}M Probability-Weighted</text>
"""
    stage_colors = ["#38bdf8", "#60a5fa", "#818cf8", "#a78bfa", "#10b981", "#f43f5e"]
    max_opp = max(s["opportunity_value"] for s in stages)
    for i, s in enumerate(stages):
        y = 110 + i * 64
        w = int((s["opportunity_value"] / max_opp) * 320)
        col = stage_colors[i % len(stage_colors)]
        svg_crm += f"""
  <rect x="636" y="{y}" width="516" height="50" rx="8" fill="#0f172a" stroke="#334155" stroke-width="0.8"/>
  <rect x="636" y="{y}" width="8" height="50" rx="4" fill="{col}"/>
  <text x="656" y="{y+22}" fill="#f8fafc" font-size="14" font-weight="700">{s['Sales Stage']}</text>
  <text x="656" y="{y+40}" fill="#94a3b8" font-size="11">{s['leads']} Deals in Stage</text>
  <rect x="800" y="{y+16}" width="210" height="18" rx="5" fill="#1e293b"/>
  <rect x="800" y="{y+16}" width="{int(w*0.65)}" height="18" rx="5" fill="{col}" opacity="0.85"/>
  <text x="1025" y="{y+24}" fill="#f8fafc" font-size="12" font-weight="700">${s['opportunity_value']/1e6:.2f}M</text>
  <text x="1025" y="{y+41}" fill="{col}" font-size="11" font-weight="600">Exp: ${s['expected_revenue']/1e3:.0f}K</text>"""

    svg_crm += "\n</svg>"
    (CHARTS_DIR / "crm_pipeline_and_sales.svg").write_text(svg_crm, encoding="utf-8")

    # 3. Warehouse Heatmap & Supplier Risk SVG Preview
    svg_wh = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 440" width="100%" height="100%" font-family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">
  <rect width="1200" height="440" rx="16" fill="#0b0f19"/>
  <rect x="24" y="24" width="1152" height="392" rx="12" fill="#1e293b" stroke="#334155"/>
  <text x="48" y="58" fill="#f8fafc" font-size="18" font-weight="700">Warehouse Capital Distribution &amp; Stockout Risk Matrix</text>
  <text x="48" y="78" fill="#94a3b8" font-size="12">Comparing Inventory Asset Value, Total Revenue Generated, and Low-Stock Alerts across 8 Fulfillment Centers</text>
"""
    for i, w in enumerate(whs):
        col_idx = i % 4
        row_idx = i // 4
        x = 48 + col_idx * 278
        y = 104 + row_idx * 145
        svg_wh += f"""
  <rect x="{x}" y="{y}" width="260" height="128" rx="10" fill="#0f172a" stroke="#334155"/>
  <text x="{x+18}" y="{y+28}" fill="#38bdf8" font-size="15" font-weight="700">{w['Warehouse Location']}</text>
  <text x="{x+185}" y="{y+28}" fill="#94a3b8" font-size="12">{w['skus']} SKUs</text>
  <text x="{x+18}" y="{y+58}" fill="#f8fafc" font-size="22" font-weight="800">${w['stock_value']/1e3:.1f}K</text>
  <text x="{x+18}" y="{y+76}" fill="#64748b" font-size="11">Inventory Asset Value ({w['units_in_stock']:,} units)</text>
  <text x="{x+18}" y="{y+104}" fill="#10b981" font-size="12" font-weight="600">Rev: ${w['revenue']/1e6:.2f}M</text>
  <text x="{x+145}" y="{y+104}" fill="#f59e0b" font-size="12" font-weight="600">⚠ {w['low_stock']} Low Stock</text>"""

    svg_wh += "\n</svg>"
    (CHARTS_DIR / "warehouse_capital_matrix.svg").write_text(svg_wh, encoding="utf-8")


def main():
    payload = build_analytics_payload()
    json_path = BASE_DIR / "dashboard_data.json"
    js_path = BASE_DIR / "dashboard_data.js"

    json_str = json.dumps(payload, indent=2)
    json_path.write_text(json_str, encoding="utf-8")
    js_path.write_text(f"window.BI_DASHBOARD_DATA = {json_str};\n", encoding="utf-8")

    generate_svg_chart_previews(payload)

    inv_kpis = payload["inventory_kpis"]
    crm_kpis = payload["crm_kpis"]
    print("ETL Pipeline Complete!")
    print(f"Inventory SKUs: {inv_kpis['total_skus']} | Revenue: ${inv_kpis['total_revenue']:,.2f} | Profit: ${inv_kpis['total_profit']:,.2f} ({inv_kpis['avg_profit_margin']}%)")
    print(f"Inventory Cost Value: ${inv_kpis['total_inventory_cost_value']:,.2f} | Low Stock SKUs: {inv_kpis['low_stock_skus']}")
    print(f"CRM Customers: {crm_kpis['total_customers']} | Transactions: {crm_kpis['total_orders']} | CRM Rev: ${crm_kpis['tx_total_revenue']:,.2f}")
    print(f"Pipeline Opportunity: ${crm_kpis['pipeline_total_opportunity']:,.2f} | Expected: ${crm_kpis['pipeline_expected_revenue']:,.2f}")


if __name__ == "__main__":
    main()
