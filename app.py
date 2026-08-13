import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(page_title="Cashflow Forecast Engine", layout="wide")

st.title("💸 Daily Cashflow Forecast Engine")

# --- SIDEBAR: CORE SETTINGS ---
st.sidebar.header("1. Core Settings")

start_balance = st.sidebar.number_input(
    "Starting Account Balance (£)", 
    value=1500.00, 
    step=100.00
)

forecast_days = st.sidebar.slider(
    "Forecast Horizon (Days)", 
    min_value=30, 
    max_value=365, 
    value=90
)

buffer_threshold = st.sidebar.number_input(
    "Minimum Safety Buffer (£)", 
    value=500.00, 
    step=50.00
)

# --- SIDEBAR: RECURRING RULES CONFIGURATOR ---
st.sidebar.header("2. Recurring Income & Bills")

if 'rules' not in st.session_state:
    st.session_state.rules = [
        {"name": "Employer Payroll", "amount": 2400.00, "day": 25, "type": "Income"},
        {"name": "Landlord Rent", "amount": 850.00, "day": 1, "type": "Bill"},
        {"name": "Council Tax", "amount": 150.00, "day": 5, "type": "Bill"},
        {"name": "Utilities & Wifi", "amount": 120.00, "day": 15, "type": "Bill"}
    ]

with st.sidebar.expander("➕ Add Custom Rule"):
    rule_name = st.text_input("Description", "Gym Membership")
    rule_amount = st.number_input("Amount (£)", value=35.00, step=5.00)
    rule_day = st.number_input("Day of Month (1-31)", min_value=1, max_value=31, value=10)
    rule_type = st.selectbox("Type", ["Bill", "Income"])
    
    if st.button("Add Rule"):
        st.session_state.rules.append({
            "name": rule_name,
            "amount": rule_amount,
            "day": rule_day,
            "type": rule_type
        })
        st.success(f"Added {rule_name}!")

# --- CSV STATEMENT UPLOADER ---
st.subheader("Import Historical Bank Statement (Optional)")
uploaded_file = st.file_uploader("Upload bank statement (CSV with 'Date' and 'Amount' columns)", type=["csv"])

daily_discretionary_spend = 0.0

if uploaded_file is not None:
    try:
        csv_df = pd.read_csv(uploaded_file)
        csv_df.columns = csv_df.columns.str.strip().str.capitalize()
        
        if 'Date' in csv_df.columns and 'Amount' in csv_df.columns:
            csv_df['Date'] = pd.to_datetime(csv_df['Date'])
            
            debits = csv_df[csv_df['Amount'] < 0]
            total_days = (csv_df['Date'].max() - csv_df['Date'].min()).days or 30
            daily_discretionary_spend = abs(debits['Amount'].sum()) / total_days
            
            st.info(f"📊 Estimated daily variable spend: **£{daily_discretionary_spend:.2f}/day** based on {total_days} days of statement history.")
        else:
            st.warning("CSV must contain 'Date' and 'Amount' headers. Falling back to default rules.")
    except Exception as e:
        st.error(f"Error parsing CSV: {e}")

# --- FORECAST TIMELINE ENGINE ---
start_date = pd.Timestamp.today().normalize()
date_range = pd.date_range(start=start_date, periods=forecast_days, freq="D")

df = pd.DataFrame({'date': date_range})
df['income'] = 0.0
df['bills'] = 0.0
df['variable_spend'] = daily_discretionary_spend

# Apply recurring rules
for rule in st.session_state.rules:
    mask = df['date'].dt.day == rule['day']
    if rule['type'] == "Income":
        df.loc[mask, 'income'] += rule['amount']
    else:
        df.loc[mask, 'bills'] += rule['amount']

df['net_flow'] = df['income'] - df['bills'] - df['variable_spend']
df['Baseline Balance'] = start_balance + df['net_flow'].cumsum()

# --- WHAT-IF SCENARIO SIMULATOR ---
st.markdown("---")
st.subheader("🧪 What-If Scenario Simulator")

enable_scenario = st.checkbox("Enable Scenario Testing Overlay")

if enable_scenario:
    col_sc1, col_sc2, col_sc3 = st.columns(3)
    
    scenario_event = col_sc1.text_input("Scenario Description", "Weekend Trip / Holiday")
    scenario_amount = col_sc2.number_input("One-off Event Amount (£)", value=350.00, step=50.00)
    scenario_day_offset = col_sc3.number_input("Occurs in (Days from today)", min_value=1, max_value=forecast_days, value=14)
    
    # Calculate scenario balance
    df['Scenario Impact'] = 0.0
    if scenario_day_offset <= len(df):
        df.loc[scenario_day_offset - 1, 'Scenario Impact'] = -scenario_amount
        
    df['Simulated Balance'] = start_balance + (df['net_flow'] + df['Scenario Impact']).cumsum()
    
    # Check scenario impact on safety buffer
    sim_min = df['Simulated Balance'].min()
    sim_min_date = df.loc[df['Simulated Balance'].idxmin(), 'date'].strftime('%d %b %Y')
    
    if sim_min < buffer_threshold:
        st.error(f"🚨 **Scenario Alert:** Under '{scenario_event}', balance drops to **£{sim_min:,.2f}** on **{sim_min_date}**, breaching your £{buffer_threshold:,.2f} safety buffer!")
    else:
        st.success(f"✅ **Scenario Safe:** Lowest projected balance with '{scenario_event}' is **£{sim_min:,.2f}** on **{sim_min_date}**.")

# --- METRICS DISPLAY ---
col1, col2, col3 = st.columns(3)
col1.metric("Starting Balance", f"£{start_balance:,.2f}")
baseline_min = df['Baseline Balance'].min()
col2.metric("Baseline Lowest Point", f"£{baseline_min:,.2f}")
col3.metric("Ending Balance", f"£{df['Baseline Balance'].iloc[-1]:,.2f}")

# --- CHART VISUALIZATION ---
st.subheader("Cashflow Projection Chart")

if enable_scenario:
    st.line_chart(df.set_index('date')[['Baseline Balance', 'Simulated Balance']])
else:
    st.line_chart(df.set_index('date')[['Baseline Balance']])

# --- DATA BREAKDOWN TABLE ---
st.subheader("Detailed Projections")
display_cols = ['date', 'income', 'bills', 'variable_spend', 'Baseline Balance']
if enable_scenario:
    display_cols.append('Simulated Balance')

st.dataframe(
    df[display_cols].style.format({
        'income': '£{:,.2f}',
        'bills': '£{:,.2f}',
        'variable_spend': '£{:,.2f}',
        'Baseline Balance': '£{:,.2f}',
        'Simulated Balance': '£{:,.2f}' if enable_scenario else '{}'
    }),
    use_container_width=True
)