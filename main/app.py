import streamlit as st
import sys
import os

# --- PATH RESOLUTION FOR MAIN SUBFOLDER ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- MODULE IMPORTS ---
try:
    from core.db import init_db
    import views.tab_overview as tab_overview
    import views.tab_scenarios as tab_scenarios
    import views.tab_payoff as tab_payoff
    import views.tab_categories as tab_categories
    import views.tab_feedback as tab_feedback
    import views.tab_knowledge as tab_knowledge
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

def execute_tab(module, primary_func_name):
    """Safely executes the tab function (e.g., render_overview_tab) or falls back to generic entry points."""
    possible_funcs = [
        primary_func_name,
        f"render_{module.__name__.split('.')[-1]}",
        "show",
        "render",
        "display",
        "main",
        "run"
    ]
    for func_name in possible_funcs:
        if hasattr(module, func_name):
            getattr(module, func_name)()
            return
    st.error(f"Could not locate an execution function in module {module.__name__}.")

def main():
    # Database setup
    try:
        init_db()
    except Exception as db_err:
        st.warning(f"Database initialization notice: {db_err}")

    st.title("📈 Cashflow Forecasting & Financial Engine")

    # --- TOP TAB NAVIGATION LAYOUT ---
    t_overview, t_scenarios, t_payoff, t_categories, t_feedback, t_knowledge = st.tabs([
        "📊 Overview Dashboard",
        "🔮 Scenario Planning",
        "💳 Debt Payoff Strategy",
        "🏷️ Categories & Budgets",
        "💬 Feedback & Insights",
        "📚 Knowledge Base"
    ])

    with t_overview:
        execute_tab(tab_overview, "render_overview_tab")

    with t_scenarios:
        execute_tab(tab_scenarios, "render_scenarios_tab")

    with t_payoff:
        execute_tab(tab_payoff, "render_payoff_tab")

    with t_categories:
        execute_tab(tab_categories, "render_categories_tab")

    with t_feedback:
        execute_tab(tab_feedback, "render_feedback_tab")

    with t_knowledge:
        execute_tab(tab_knowledge, "render_knowledge_tab")

if __name__ == "__main__":
    try:
        main()
    except Exception as app_err:
        st.error(f"A runtime error occurred in the application: {app_err}")
        import traceback
        st.code(traceback.format_exc())