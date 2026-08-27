import streamlit as st
import sys
import os

# Ensure the root directory is in the path for modular imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- CRITICAL STARTUP ERROR TRAP ---
try:
    from core.database import init_db
    # Uncomment and adjust these imports based on your exact view file names
    # from views import tab_overview, tab_forecast, tab_scenarios, tab_settings
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
        ["Overview Dashboard", "Cashflow Projections", "Scenario Planning", "Settings & Data"]
    )

    st.sidebar.divider()
    st.sidebar.caption("Cashflow Forecasting Engine v1.0")

    # --- MAIN VIEW ROUTING ---
    if app_mode == "Overview Dashboard":
        st.title("📊 Overview Dashboard")
        st.write("Welcome to your financial insights hub. Your core metrics and summary are loading below.")
        # Call your view function here, e.g.: tab_overview.render()
        
    elif app_mode == "Cashflow Projections":
        st.title("💸 Cashflow Projections")
        st.write("Detailed transaction tracking and future forecasting.")
        # Call your view function here, e.g.: tab_forecast.render()
        
    elif app_mode == "Scenario Planning":
        st.title("🔮 Scenario Planning & Stress Testing")
        st.write("Simulate financial choices and evaluate future adjustments.")
        # Call your view function here, e.g.: tab_scenarios.render()
        
    elif app_mode == "Settings & Data":
        st.title("⚙️ Settings & Data Management")
        st.write("Manage your baseline inputs, categories, and data sources.")
        # Call your view function here, e.g.: tab_settings.render()

if __name__ == "__main__":
    try:
        main()
    except Exception as app_err:
        st.error(f"A runtime error occurred in the application: {app_err}")
        import traceback
        st.code(traceback.format_exc())