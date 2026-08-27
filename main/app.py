import streamlit as st
import sys
import os

# --- PATH FIX FOR MODULAR IMPORTS ---
# Ensures Python can locate your core/ and views/ directories from inside the main/ folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- CRITICAL STARTUP ERROR TRAP ---
try:
    from core.db import init_db
    # Add your view imports here safely
    # from views import tab_overview, tab_forecast, tab_scenarios, tab_categories, tab_payoff, tab_feedback, tab_knowledge
except Exception as e:
    st.error(f"CRITICAL MODULE IMPORT ERROR: {e}")
    import traceback
    st.code(traceback.format_exc())
    st.stop()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Cashflow Forecasting & Planning",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    try:
        # Initialize database safely on startup
        init_db()
    except Exception as db_err:
        st.warning(f"Database initialization notice: {db_err}")

    # --- SIDEBAR NAVIGATION & CONTROLS ---
    st.sidebar.title("Navigation & Controls")
    
    app_mode = st.sidebar.radio(
        "Select View",
        [
            "Overview Dashboard", 
            "Cashflow Projections", 
            "Scenario Planning", 
            "Debt Payoff Strategy", 
            "Categories & Budgets", 
            "Feedback & Insights"
        ]
    )

    st.sidebar.divider()
    st.sidebar.caption("Cashflow Forecasting Engine v1.0")

    # --- MAIN VIEW ROUTING ---
    if app_mode == "Overview Dashboard":
        st.title("📊 Overview Dashboard")
        st.write("Welcome to your financial insights hub.")
        # tab_overview.render()
        
    elif app_mode == "Cashflow Projections":
        st.title("💸 Cashflow Projections")
        st.write("Detailed transaction tracking and future forecasting.")
        # tab_forecast.render()
        
    elif app_mode == "Scenario Planning":
        st.title("🔮 Scenario Planning & Stress Testing")
        st.write("Simulate financial choices and evaluate future adjustments.")
        # tab_scenarios.render()

    elif app_mode == "Debt Payoff Strategy":
        st.title("💳 Debt Management & Payoff")
        st.write("Review avalanche and snowball payoff schedules.")
        # tab_payoff.render()

    elif app_mode == "Categories & Budgets":
        st.title("🏷️ Categories & Budgets")
        st.write("Manage your transaction categories and allocation targets.")
        # tab_categories.render()

    elif app_mode == "Feedback & Insights":
        st.title("💬 Feedback & System Notes")
        st.write("Log feedback and explore system reference knowledge.")
        # tab_feedback.render()

if __name__ == "__main__":
    try:
        main()
    except Exception as app_err:
        st.error(f"A runtime error occurred in the application: {app_err}")
        import traceback
        st.code(traceback.format_exc())