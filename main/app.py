import streamlit as st
import sys
import os

# --- PATH FIX FOR MODULAR IMPORTS ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- IMPORT MODULES ---
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

def render_view_module(module):
    """Dynamically finds and executes whatever entry function the view file uses."""
    for fn_name in ["show", "display", "render", "main", "render_tab", "run"]:
        if hasattr(module, fn_name):
            getattr(module, fn_name)()
            return
    st.error(f"Could not find a valid execution function (like show() or render()) in module: {module.__name__}")

def main():
    try:
        init_db()
    except Exception as db_err:
        st.warning(f"Database initialization notice: {db_err}")

    # --- SIDEBAR NAVIGATION ---
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

    # --- ROUTING ---
    if app_mode == "Overview Dashboard":
        render_view_module(tab_overview)
        
    elif app_mode == "Scenario Planning":
        render_view_module(tab_scenarios)

    elif app_mode == "Debt Payoff Strategy":
        render_view_module(tab_payoff)

    elif app_mode == "Categories & Budgets":
        render_view_module(tab_categories)

    elif app_mode == "Feedback & Insights":
        render_view_module(tab_feedback)

    elif app_mode == "Knowledge Base":
        render_view_module(tab_knowledge)

if __name__ == "__main__":
    try:
        main()
    except Exception as app_err:
        st.error(f"A runtime error occurred in the application: {app_err}")
        import traceback
        st.code(traceback.format_exc())