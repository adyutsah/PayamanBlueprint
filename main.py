"""
views/overview.py
------------------
Executive Overview — a read-only dashboard summarizing the logged-in
user's net worth, monthly surplus, investments, and progress toward
their wealth target, plus a 15-year compounding projection and asset
allocation breakdown.

Reads exclusively from:
  - data/{email}_finances.csv  (via utils.load_finances)
  - data/{email}_ledger.csv    (via utils.load_ledger)
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import sys
import os

# Ensure the project root (parent of views/) is on sys.path so `import utils`
# resolves regardless of Streamlit Cloud's working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils

email = st.session_state.get("user_email")
name = st.session_state.get("user_name", "Investor")

st.title("📊 Executive Overview")
st.caption(f"Welcome back, {name}. Here's your wealth snapshot.")

# ---------------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------------
finances = utils.load_finances(email)
ledger = utils.load_ledger(email)

row = finances.iloc[0]
monthly_income = float(row.get("monthly_income", 0) or 0)
liquid_savings = float(row.get("liquid_savings", 0) or 0)
investments = float(row.get("investments", 0) or 0)
other_assets = float(row.get("other_assets", 0) or 0)
target_goal = float(row.get("target_goal", 0) or 0)
growth_rate = float(row.get("growth_rate", 8.0) or 8.0)

net_worth = liquid_savings + investments + other_assets

# ---------------------------------------------------------------------------
# DERIVE MONTHLY SURPLUS FROM THE LEDGER
# (Base Monthly Income minus this calendar month's logged expenses)
# ---------------------------------------------------------------------------
ledger_clean = ledger.copy()
if not ledger_clean.empty:
    ledger_clean["date"] = pd.to_datetime(ledger_clean["date"], errors="coerce")
    ledger_clean["amount"] = pd.to_numeric(ledger_clean["amount"], errors="coerce").fillna(0)

    current_period = pd.Timestamp.now().to_period("M")
    this_month_df = ledger_clean[ledger_clean["date"].dt.to_period("M") == current_period]
    expenses_this_month = this_month_df.loc[this_month_df["type"] == "Expense", "amount"].sum()
else:
    expenses_this_month = 0.0

monthly_surplus = monthly_income - expenses_this_month

# ---------------------------------------------------------------------------
# TOP ROW — 4 METRIC CARDS + PROGRESS BAR
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Net Worth", f"₱{net_worth:,.2f}")
c2.metric("Monthly Surplus", f"₱{monthly_surplus:,.2f}")
c3.metric("Total Investments", f"₱{investments:,.2f}")
c4.metric("Target Goal", f"₱{target_goal:,.2f}")

if target_goal > 0:
    progress_pct = max(0.0, min(net_worth / target_goal, 1.0))
    st.progress(progress_pct, text=f"{progress_pct * 100:.1f}% of the way to your ₱{target_goal:,.0f} target")
else:
    st.info("Set an Ultimate Wealth Target on the Financial Profile page to track progress here.")

st.markdown("---")

# ---------------------------------------------------------------------------
# MIDDLE ROW — 15-YEAR PROJECTION (2/3) + ASSET ALLOCATION DONUT (1/3)
# ---------------------------------------------------------------------------
left, right = st.columns([2, 1])

with left:
    st.subheader("📈 15-Year Wealth Projection")

    years = np.arange(0, 16)
    annual_surplus = max(monthly_surplus, 0) * 12
    r = growth_rate / 100.0

    projected_values = []
    for y in years:
        # Future value of the existing pool, compounded annually
        pool_fv = net_worth * ((1 + r) ** y)
        # Future value of an ordinary annuity from annual surplus contributions
        if r > 0:
            contrib_fv = annual_surplus * (((1 + r) ** y - 1) / r)
        else:
            contrib_fv = annual_surplus * y
        projected_values.append(pool_fv + contrib_fv)

    proj_df = pd.DataFrame({"Year": years, "Projected Net Worth": projected_values})

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=proj_df["Year"],
            y=proj_df["Projected Net Worth"],
            fill="tozeroy",
            mode="lines",
            name="Projected Net Worth",
            line=dict(color="#6366f1", width=3),
            fillcolor="rgba(99, 102, 241, 0.15)",
        )
    )
    if target_goal > 0:
        fig.add_hline(
            y=target_goal,
            line_dash="dash",
            line_color="#ef4444",
            annotation_text="Target Goal",
            annotation_position="top left",
        )
    fig.update_layout(
        template="plotly_white",
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis_title="Net Worth (₱)",
        xaxis_title="Years From Now",
        showlegend=False,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Assumes a {growth_rate:.1f}% annual growth rate on your current ₱{net_worth:,.0f} pool, "
        f"plus ₱{annual_surplus:,.0f}/year in new contributions from your current surplus."
    )

with right:
    st.subheader("🥧 Asset Allocation")
    alloc_df = pd.DataFrame(
        {
            "Asset": ["Savings", "Investments", "Other Assets"],
            "Value": [liquid_savings, investments, other_assets],
        }
    )
    if alloc_df["Value"].sum() > 0:
        fig2 = px.pie(
            alloc_df,
            names="Asset",
            values="Value",
            hole=0.55,
            color="Asset",
            color_discrete_map={
                "Savings": "#6366f1",
                "Investments": "#22c55e",
                "Other Assets": "#f59e0b",
            },
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        fig2.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No assets recorded yet. Head to the Financial Profile page to set them up.")

st.markdown("---")

# ---------------------------------------------------------------------------
# BOTTOM ROW — LAST 5 SAVINGS/ASSET ENTRIES | LAST 5 EXPENSES
# ---------------------------------------------------------------------------
bcol1, bcol2 = st.columns(2)

with bcol1:
    st.subheader("💰 Recent Savings / Assets")
    if not ledger_clean.empty:
        assets_recent = (
            ledger_clean[ledger_clean["type"] == "Asset/Savings"]
            .sort_values("date", ascending=False)
            .head(5)
        )
        if not assets_recent.empty:
            display_df = assets_recent[["date", "category", "amount"]].copy()
            display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_df, hide_index=True, use_container_width=True)
        else:
            st.caption("No savings/asset entries logged yet.")
    else:
        st.caption("No transactions logged yet. Visit the Transaction Ledger page to add one.")

with bcol2:
    st.subheader("💸 Recent Expenses")
    if not ledger_clean.empty:
        expenses_recent = (
            ledger_clean[ledger_clean["type"] == "Expense"]
            .sort_values("date", ascending=False)
            .head(5)
        )
        if not expenses_recent.empty:
            display_df = expenses_recent[["date", "category", "amount"]].copy()
            display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_df, hide_index=True, use_container_width=True)
        else:
            st.caption("No expenses logged yet.")
    else:
        st.caption("No transactions logged yet. Visit the Transaction Ledger page to add one.")
