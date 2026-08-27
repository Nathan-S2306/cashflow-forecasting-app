import streamlit as st
from core.db import export_system_data, import_system_data, init_db
from core.importer import process_bank_import
from views.tab_categories import render_categories_tab
from views.tab_feedback import render_feedback_tab
from views.tab_knowledge import render_knowledge_tab
from views.tab_overview import render_overview_tab
from views.tab_payoff import render_payoff_tab
from views.tab_scenarios import render_scenarios_tab

st.set_page_config(page_title="Personal Cashflow Engine", page_icon="💰", layout="wide")

# Initialize SQLite database schema
init_db()

st.title("💰 Cashflow Engine & Money Hub")

st.sidebar.title("⚙️ Engine Controls")

# Bank Statement Upload
with st.sidebar.expander("📥 Import Bank Statement CSV"):
    uploaded_bank_file = st.file_uploader("Upload Bank CSV", type=["csv"], key="bank_upload")
    import_mode = st.radio("Import as:", ["Recurring Rules", "One-Off Purchases"], key="bank_mode")

    if uploaded_bank_file and st.button("Process & Import Statement"):
        try:
            mode_key = "recurring" if import_mode == "Recurring Rules" else "one_off"
            inc_cnt, exp_cnt = process_bank_import(uploaded_bank_file, import_type=mode_key)
            st.success(f"Imported {inc_cnt} incomes and {exp_cnt} expenses successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error parsing statement: {e}")

# Backup Import / Export
with st.sidebar.expander("💾 System Backup & Restore"):
    if st.button("Export Backup (JSON)"):
        json_data = export_system_data()
        st.download_button("Download JSON Backup", json_data, file_name="cashflow_backup.json", mime="application/json")

    uploaded_backup = st.file_uploader("Restore JSON Backup", type=["json"], key="json_backup")
    if uploaded_backup and st.button("Restore System Data"):
        try:
            import_system_data(uploaded_backup.read().decode("utf-8"))
            st.success("System restored successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Restore failed: {e}")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Money Summary",
    "🏷️ Where Money Goes",
    "🎯 Debts & Savings Goals",
    "🧪 What-If Planning",
    "📚 Knowledge Hub",
    "💬 Feedback Log",
])

with tab1:
    render_overview_tab()
with tab2:
    render_categories_tab()
with tab3:
    render_payoff_tab()
with tab4:
    render_scenarios_tab()
with tab5:
    render_knowledge_tab()
with tab6:
    render_feedback_tab()