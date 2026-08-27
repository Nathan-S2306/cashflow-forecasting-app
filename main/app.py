import streamlit as st
import sys
import os

# --- PATH FIX FOR MODULAR IMPORTS ---
# Ensures Python can locate your core/ and views/ directories from inside the main/ folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- IMPORT DATABASE & VIEW MODULES ---
try:
    from core.db import init_db
    from views import (
        tab_overview,
        tab_scenarios,
        tab_payoff,
        tab_categories,
        tab_feedback,
        tab_knowledge
    )
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
    # Initialize database on startup
    try:
        init_db()
    except Exception as db_err:
        st.warning(f"Database initialization notice: {db_err}")

    # --- SIDEBAR NAVIGATION & CONTROLS ---
    st.sidebar.title("Navigation & Controls")
    
    app_mode = st.sidebar.radio(
        "Select View",
        [
            "Overview Dashboard", 
            "Scenario Planning", 
            "Debt Payoff Strategy", 
            "Categories & Budgets", 
            "Feedback & Insights",
            "Knowledge Base"
        ]
    )

    st.sidebar.divider()
    st.sidebar.caption("Cashflow Forecasting Engine v1.0")

    # --- MAIN VIEW ROUTING ---
    if app_mode == "Overview Dashboard":
        tab_overview.render()
        
    elif app_mode == "Scenario Planning":
        tab_scenarios.render()

    elif app_mode == "Debt Payoff Strategy":
        tab_payoff.render()

    elif app_mode == "Categories & Budgets":
        tab_categories.render()

    elif app_mode == "Feedback & Insights":
        tab_feedback.render()

    elif app_mode == "Knowledge Base":
        tab_knowledge.render()

if __name__ == "__main__":
    try:
        main()
    except Exception as app_err:
        st.error(f"A runtime error occurred in the application: {app_err}")
        import traceback
        st.code(traceback.format_exc())