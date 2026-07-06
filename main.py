import streamlit as st
import pandas as pd
import numpy as np
import os
import hashlib

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Payaman Blueprint", page_icon="💰", layout="wide")

st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem;}
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }
    </style>
""", unsafe_allow_html=True)

DATA_DIR = "data"
USERS_FILE = "users.csv"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- HELPER FUNCTIONS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            return pd.read_csv(USERS_FILE).to_dict(orient="records")
        except Exception:
            return []
    return []

def save_user(email, password):
    users = load_users()
    if any(u['email'] == email for u in users):
        return False
    new_user = {"email": email, "password": hash_password(password)}
    users.append(new_user)
    pd.DataFrame(users).to_csv(USERS_FILE, index=False)
    return True

def verify_user(email, password):
    users = load_users()
    hashed = hash_password(password)
    return any(u['email'] == email and u['password'] == hashed for u in users)

def get_user_file(email):
    safe_name = email.replace("@", "_").replace(".", "_")
    return os.path.join(DATA_DIR, f"{safe_name}_finances.csv")

def load_user_data(email):
    filepath = get_user_file(email)
    if os.path.exists(filepath):
        try:
            return pd.read_csv(filepath).iloc[0].to_dict()
        except Exception:
            pass
    return {
        "monthly_income": 5000.0, "monthly_expense": 3000.0,
        "savings_balance": 10000.0, "investment_balance": 25000.0,
        "other_assets": 5000.0, "annual_return": 7.0, "target_amount": 500000.0
    }

def save_user_data(email, data):
    filepath = get_user_file(email)
    pd.DataFrame([data]).to_csv(filepath, index=False)

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = ""

# --- AUTHENTICATION INTERFACE ---
if not st.session_state.authenticated:
    st.title("🔒 Payaman Blueprint - Portal")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        login_email = st.text_input("Email Address", key="l_email")
        login_pass = st.text_input("Password", type="password", key="l_pass")
        if st.button("Sign In", type="primary"):
            if verify_user(login_email, login_pass):
                st.session_state.authenticated = True
                st.session_state.user_email = login_email
                st.rerun()
            else:
                st.error("Invalid email or password.")
                
    with tab2:
        reg_email = st.text_input("Email Address", key="r_email")
        reg_pass = st.text_input("Password", type="password", key="r_pass")
        if st.button("Create Account"):
            if reg_email and reg_pass:
                if save_user(reg_email, reg_pass):
                    st.success("Account created successfully! Please log in.")
                else:
                    st.error("User already exists.")
            else:
                st.error("Please fill in all fields.")
    st.stop()

# --- DASHBOARD LOGIC ---
user_email = st.session_state.user_email
user_data = load_user_data(user_email)

with st.sidebar:
    st.subheader(f"👤 {user_email}")
    if st.button("Log Out", type="secondary", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.rerun()
    st.markdown("---")
    st.subheader("🛠️ Quick Data Update")
    
    inc = st.number_input("Monthly Income ($)", value=float(user_data["monthly_income"]), step=100.0)
    exp = st.number_input("Monthly Expenses ($)", value=float(user_data["monthly_expense"]), step=100.0)
    sav = st.number_input("Current Savings ($)", value=float(user_data["savings_balance"]), step=500.0)
    inv = st.number_input("Current Investments ($)", value=float(user_data["investment_balance"]), step=500.0)
    ast = st.number_input("Other Assets ($)", value=float(user_data["other_assets"]), step=500.0)
    ret = st.slider("Expected Annual Return (%)", 0.0, 20.0, float(user_data["annual_return"]), 0.5)
    tgt = st.number_input("Financial Target Milestone ($)", value=float(user_data["target_amount"]), step=10000.0)
    
    if st.button("Save Changes", type="primary", use_container_width=True):
        updated_data = {
            "monthly_income": inc, "monthly_expense": exp, "savings_balance": sav,
            "investment_balance": inv, "other_assets": ast, "annual_return": ret, "target_amount": tgt
        }
        save_user_data(user_email, updated_data)
        st.success("Data synced successfully!")
        st.rerun()

st.title("📈 Payaman Blueprint Personal Advisor Dashboard")

monthly_surplus = inc - exp
annual_savings_contribution = monthly_surplus * 12
total_net_worth = sav + inv + ast

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Net Worth", f"${total_net_worth:,.2f}")
with col2:
    st.metric("Monthly Surplus", f"${monthly_surplus:,.2f}", delta=f"{(monthly_surplus/inc)*100:.1f}% Savings" if inc > 0 else None)
with col3:
    st.metric("Current Investments", f"${inv:,.2f}")
with col4:
    st.metric("Target Milestone", f"${tgt:,.2f}")

st.markdown("---")

tab_overview, tab_projection = st.tabs(["📊 Current Asset Breakdown", "🔮 30-Year Compounding Projection"])

with tab_overview:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Portfolio Composition")
        breakdown_df = pd.DataFrame({
            "Asset Type": ["Savings", "Investments", "Other Assets"],
            "Value ($)": [sav, inv, ast]
        })
        st.dataframe(breakdown_df, hide_index=True, use_container_width=True)
    with c2:
        st.subheader("Visual Distribution")
        st.bar_chart(breakdown_df, x="Asset Type", y="Value ($)")

with tab_projection:
    st.subheader("The Power of Compounding")
    years = st.slider("Projection Horizon (Years)", 5, 50, 20)
    
    r = ret / 100
    projection_list = []
    current_inv_pool = inv + sav
    
    for year in range(0, years + 1):
        if year == 0:
            future_value = current_inv_pool
        else:
            future_value = (current_inv_pool * ((1 + r) ** year)) + (annual_savings_contribution * (((1 + r) ** year - 1) / r) if r > 0 else annual_savings_contribution * year)
        
        projection_list.append({
            "Year": year,
            "Projected Wealth ($)": round(future_value, 2),
            "Target Milestone ($)": tgt
        })
        
    df_proj = pd.DataFrame(projection_list).set_index("Year")
    
    milestone_hit = df_proj[df_proj["Projected Wealth ($)"] >= tgt]
    if not milestone_hit.empty:
        st.success(f"🎉 **Advisor Tip:** You will hit your **${tgt:,.2f}** target in **{milestone_hit.index[0]} years**!")
    else:
        st.warning(f"⚠️ **Advisor Tip:** You will not hit your target within {years} years at your current rate.")

    st.line_chart(df_proj, y=["Projected Wealth ($)", "Target Milestone ($)"])
