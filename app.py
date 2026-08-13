import requests
import pandas as pd
import numpy as np
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(page_title="Cashflow Forecast Engine", layout="wide")

st.title("💸 Daily Cashflow Forecast Engine")

# =====================================================================
# SIDEBAR CONFIGURATION
# =====================================================================

# 1. CORE SETTINGS
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

# 2. RECURRING INCOME & BILLS CONFIGURATOR
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

# Display current active rules in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Active Rules")
for idx, r in enumerate(st.session_state.rules):
    st.sidebar.caption(f"• **{r['name']}**: £{r['amount']:.2f} (Day {r['day']}) [{r['type']}]")

# =====================================================================
# MAIN TAB NAVIGATION
# =====================================================================
tab_dashboard, tab_guide, tab_feedback = st.tabs([
    "📊 Forecast Dashboard", 
    "📖 How to Use Guide", 
    "💬 Leave Feedback"
])

# =====================================================================
# TAB 1: MAIN FORECAST DASHBOARD
# =====================================================================
with tab_dashboard:
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

    # Apply recurring rules across the timeline
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
        
        # Calculate scenario impact
        df['Scenario Impact'] = 0.0
        if scenario_day_offset <= len(df):
            df.loc[scenario_day_offset - 1, 'Scenario Impact'] = -scenario_amount
            
        df['Simulated Balance'] = start_balance + (df['net_flow'] + df['Scenario Impact']).cumsum()
        
        # Check buffer breach
        sim_min = df['Simulated Balance'].min()
        sim_min_date = df.loc[df['Simulated Balance'].idxmin(), 'date'].strftime('%d %b %Y')
        
        if sim_min < buffer_threshold:
            st.error(f"🚨 **Scenario Alert:** Under '{scenario_event}', balance drops to **£{sim_min:,.2f}** on **{sim_min_date}**, breaching your £{buffer_threshold:,.2f} safety buffer!")
        else:
            st.success(f"✅ **Scenario Safe:** Lowest projected balance with '{scenario_event}' is **£{sim_min:,.2f}** on **{sim_min_date}**.")

    # --- SUMMARY METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Starting Balance", f"£{start_balance:,.2f}")
    baseline_min = df['Baseline Balance'].min()
    col2.metric("Baseline Lowest Point", f"£{baseline_min:,.2f}")
    col3.metric("Ending Balance", f"£{df['Baseline Balance'].iloc[-1]:,.2f}")

    # --- VISUAL PROJECTION CHART ---
    st.subheader("Cashflow Projection Chart")

    if enable_scenario:
        st.line_chart(df.set_index('date')[['Baseline Balance', 'Simulated Balance']])
    else:
        st.line_chart(df.set_index('date')[['Baseline Balance']])

    # --- DATA TABLE BREAKDOWN ---
    st.subheader("Detailed Day-by-Day Projections")
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

# =====================================================================
# TAB 2: IN-APP "HOW TO USE" GUIDE
# =====================================================================
with tab_guide:
    st.header("📖 How to Get the Best Out of Your Cashflow Engine")
    
    st.markdown("""
    Most budgeting tools look **backward** to tell you what you already spent. This app looks **forward** to prevent overdraft surprises and show your true safe cushion.
    
    ---
    
    ### 🛠️ 1. Set Your Baseline Parameters
    * **Starting Account Balance:** Enter your current real-time bank balance in the sidebar.
    * **Forecast Horizon:** Set how far ahead you want to project (e.g., 90 days).
    * **Minimum Safety Buffer:** Set a cushion amount (e.g., £500). If your projected balance ever drops below this, the engine triggers an automatic risk alert.
    
    ---
    
    ### 📅 2. Input Your Recurring Income & Bills
    * Use **Sidebar > Add Custom Rule** to add your monthly commitments:
        * **Payday / Salary:** Set the amount and the day of the month you get paid.
        * **Fixed Bills:** Add Rent, Direct Debits, Subscriptions, and Utilities with their respective due dates.
    * *(Optional)* Upload a recent CSV statement from your bank to automatically estimate your average daily variable spend (groceries, transport, dining out).
    
    ---
    
    ### 🧪 3. Test "What-If" Purchase Scenarios
    * Thinking of making a large purchase (like booking a holiday or buying new tech)?
    * Check **Enable Scenario Testing Overlay** on the dashboard.
    * Enter the item cost and when you plan to buy it. The chart will plot a second line (**Simulated Balance**) over your baseline curve to show whether the purchase is safe or if it risks causing a low-cash warning.
    """)

# =====================================================================
# TAB 3: IN-APP FEEDBACK FORM (WEB3FORMS)
# =====================================================================
with tab_feedback:
    st.header("💬 Help Shape the Next Version")
    st.write("Your feedback helps refine the cashflow engine. Takes under 90 seconds!")

    WEB3FORMS_ACCESS_KEY = "52edad98-8b2a-4670-b77d-fb02ac367342"

    with st.form("feedback_form", clear_on_submit=True):
        ease_of_use = st.select_slider(
            "1. How easy was it to set up rules and navigate the app?",
            options=["1 - Confusing", "2 - Hard", "3 - Okay", "4 - Easy", "5 - Very Easy"],
            value="4 - Easy"
        )
        
        tested_scenario = st.radio(
            "2. Did you test the 'What-If' Scenario Simulator?",
            ["Yes, and it was clear/useful", "Yes, but it was confusing", "No, I skipped it"]
        )
        
        forward_visibility = st.radio(
            "3. Does seeing your projected minimum balance point give better visibility than your banking app?",
            ["Yes, much better forward visibility", "About the same", "No"]
        )
        
        wtp = st.radio(
            "4. If this auto-synced with your bank (via Open Banking), would you pay £3–£5/month?",
            ["Definitely yes", "Maybe, depending on extra features", "No, I prefer free manual tools"]
        )
        
        friction = st.text_area(
            "5. What was the most frustrating part or biggest friction point?",
            placeholder="e.g. Entering rules manually, CSV formatting, understanding the chart..."
        )
        
        feature = st.text_input(
            "6. What single feature should we build next?",
            placeholder="e.g. PDF Export, Mobile App, Savings Goal Tracker..."
        )
        
        email = st.text_input("Optional: Your Email (if you'd like updates)", placeholder="name@example.com")
        
        submit_button = st.form_submit_button("🚀 Submit Feedback")

        if submit_button:
            payload = {
                "access_key": WEB3FORMS_ACCESS_KEY,
                "subject": f"Cashflow App Feedback - Rating: {ease_of_use}",
                "Ease of Use": ease_of_use,
                "Tested What-If Scenario": tested_scenario,
                "Forward Visibility vs Bank": forward_visibility,
                "Willingness to Pay (£3-5/mo)": wtp,
                "Main Friction Point": friction,
                "Feature Request": feature,
                "Tester Email": email if email else "Anonymous"
            }
            
            try:
                response = requests.post("https://api.web3forms.com/submit", json=payload)
                if response.status_code == 200:
                    st.success("🎉 Thank you! Your feedback has been sent directly to my inbox.")
                else:
                    st.error("Failed to submit feedback. Please check your internet connection or try again.")
            except Exception as e:
                st.error(f"Error submitting form: {e}")