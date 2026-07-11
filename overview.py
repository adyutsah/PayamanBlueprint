"""
views/expenses.py
------------------
Transaction Ledger — a page to log cash flow (expenses and
asset/savings additions) and review the full historical log.

Writes/reads exclusively from data/{email}_ledger.csv via utils.py.
"""

from datetime import date

import pandas as pd
import streamlit as st
import sys
import os

# Ensure the project root (parent of views/) is on sys.path so `import utils`
# resolves regardless of Streamlit Cloud's working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils

email = st.session_state.get("user_email")

st.title("🧾 Transaction Ledger")
st.caption("Log every peso that moves — expenses going out, savings and investments coming in.")

# ---------------------------------------------------------------------------
# TOP — LOG A NEW TRANSACTION
# ---------------------------------------------------------------------------
with st.form("txn_form", clear_on_submit=True):
    fc1, fc2, fc3, fc4 = st.columns(4)

    with fc1:
        txn_date = st.date_input("Transaction Date", value=date.today())
    with fc2:
        txn_type = st.selectbox("Type", ["Expense", "Asset/Savings"])
    with fc3:
        category = st.text_input("Category", placeholder="e.g. Groceries, BPI Fund, Rent")
    with fc4:
        amount = st.number_input("Amount (₱)", min_value=0.0, step=100.0, format="%.2f")

    submitted = st.form_submit_button("➕ Add Transaction", use_container_width=True)

    if submitted:
        if not category.strip():
            st.error("Please provide a category before submitting.")
        elif amount <= 0:
            st.error("Amount must be greater than zero.")
        else:
            utils.append_ledger_entry(
                email=email,
                txn_date=txn_date.isoformat(),
                txn_type=txn_type,
                category=category.strip(),
                amount=amount,
            )
            st.success(f"Logged {txn_type}: ₱{amount:,.2f} under '{category.strip()}'.")
            st.rerun()

st.markdown("---")

# ---------------------------------------------------------------------------
# BOTTOM — FULL HISTORICAL LOG, NEWEST FIRST
# ---------------------------------------------------------------------------
st.subheader("📜 Full Transaction History")

ledger = utils.load_ledger(email)

if not ledger.empty:
    display_df = ledger.copy()
    display_df["date"] = pd.to_datetime(display_df["date"], errors="coerce")
    display_df = display_df.sort_values("date", ascending=False)
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")

    st.dataframe(
        display_df[["date", "type", "category", "amount"]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "amount": st.column_config.NumberColumn("Amount (₱)", format="₱%.2f"),
        },
    )

    total_expenses = ledger.loc[ledger["type"] == "Expense", "amount"].astype(float).sum()
    total_assets = ledger.loc[ledger["type"] == "Asset/Savings", "amount"].astype(float).sum()
    mcol1, mcol2 = st.columns(2)
    mcol1.metric("Total Logged Expenses", f"₱{total_expenses:,.2f}")
    mcol2.metric("Total Logged Savings/Assets", f"₱{total_assets:,.2f}")
else:
    st.info("No transactions logged yet. Add your first one above.")
