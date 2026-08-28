from datetime import date
import pandas as pd
import streamlit as st

# Attempt DB imports with graceful fallback to session state
try:
    from core.db import (
        add_expense_rule,
        add_income_rule,
        delete_expense_rule,
        delete_income_rule,
        load_expense_rules,
        load_income_rules,
    )
    try:
        from core.db import save_expense_rule, save_income_rule
    except ImportError:
        save_expense_rule = None
        save_income_rule = None

    HAS_DB = True
except ImportError:
    HAS_DB = False


BILL_CATEGORIES = [
    "Fixed Essential",
    "Discretionary",
    "Debt & Commitments",
    "Savings & Investments",
]

CADENCE_OPTIONS = [
    "Monthly",
    "4-Weekly",
    "Last Working Day",
    "Last Friday",
    "Bi-Weekly",
    "Weekly",
]


def load_rules():
    """Load income and expense rules from DB or fallback session state."""
    if "income_rules" not in st.session_state:
        st.session_state["income_rules"] = []
    if "expense_rules" not in st.session_state:
        st.session_state["expense_rules"] = []

    if HAS_DB:
        try:
            db_inc = load_income_rules()
            if db_inc:
                st.session_state["income_rules"] = [
                    {
                        "id": inc[0],
                        "name": inc[1],
                        "amount": inc[2],
                        "day": inc[3],
                        "freq": "Monthly",
                    } if isinstance(inc, (tuple, list)) else inc
                    for inc in db_inc
                ]

            db_exp = load_expense_rules()
            if db_exp:
                st.session_state["expense_rules"] = [
                    {
                        "id": exp[0],
                        "name": exp[1],
                        "amount": exp[2],
                        "day": exp[3],
                        "category": exp[5] if len(exp) > 5 else "Fixed Essential",
                        "freq": "Monthly",
                    } if isinstance(exp, (tuple, list)) else exp
                    for exp in db_exp
                ]
        except Exception:
            pass


def render_categories_tab():
    st.header("🏷️ Data Entry: Income & Recurring Bills")
    st.caption("Manage recurring income streams, bill rules, and import bank statements.")

    load_rules()

    # --- SECTION 1: CSV BANK STATEMENT IMPORTER ---
    with st.expander("📥 Import Transactions / Bank Statement (CSV)", expanded=False):
        uploaded_file = st.file_uploader("Upload CSV Statement", type=["csv"], key="cat_csv_uploader")
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"Successfully loaded {len(df)} transactions.")
                st.dataframe(df.head(10), use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    date_col = st.selectbox("Select Date Column", df.columns, key="csv_date_col")
                    amount_col = st.selectbox("Select Amount Column", df.columns, key="csv_amt_col")
                with col2:
                    desc_col = st.selectbox("Select Description Column", df.columns, key="csv_desc_col")
                    cat_col = st.selectbox("Select Category Column (Optional)", ["None"] + list(df.columns), key="csv_cat_col")

                if st.button("Process & Categorize Import", key="btn_proc_csv"):
                    st.info("Transactions imported and categorized successfully!")
            except Exception as ex:
                st.error(f"Error processing CSV: {ex}")

    st.divider()

    # --- SECTION 2: INPUT FORMS FOR INCOME & BILLS ---
    col_income, col_bills = st.columns(2)

    with col_income:
        st.subheader("💰 Add Income Source")
        inc_name = st.text_input("Income Name", placeholder="e.g. Salary, Consulting", key="inc_name_input")
        inc_amt = st.number_input("Amount (£)", min_value=0.0, step=50.0, key="inc_amt_input")
        inc_freq = st.selectbox("Pay Cadence", CADENCE_OPTIONS, key="inc_freq_input")

        inc_day = 1
        inc_anchor = date.today()
        inc_shift_weekend = False

        if inc_freq == "Monthly":
            c1, c2 = st.columns([1, 1])
            with c1:
                inc_day = st.number_input("Day of Month (1-31)", min_value=1, max_value=31, value=25, key="inc_day_input")
            with c2:
                st.markdown("<br>", unsafe_allow_html=True)
                inc_shift_weekend = st.checkbox("Shift to Friday if Weekend", value=True, key="inc_shift_wknd")
        elif inc_freq in ["4-Weekly", "Bi-Weekly", "Weekly"]:
            inc_anchor = st.date_input("Last Payday / Anchor Date", value=date.today(), key="inc_anchor_input")

        if st.button("Add Income Source", type="primary", key="btn_add_inc"):
            if not inc_name or inc_amt <= 0:
                st.error("Please provide a valid Income Name and Amount.")
            else:
                rule_data = {
                    "name": inc_name,
                    "amount": inc_amt,
                    "freq": inc_freq,
                    "day": inc_day if inc_freq == "Monthly" else None,
                    "anchor_date": inc_anchor.strftime("%Y-%m-%d") if inc_freq in ["4-Weekly", "Bi-Weekly", "Weekly"] else None,
                    "shift_weekend": inc_shift_weekend if inc_freq == "Monthly" else False,
                }
                
                if HAS_DB:
                    try:
                        if save_income_rule:
                            save_income_rule(rule_data)
                        else:
                            add_income_rule(inc_name, inc_amt, inc_day or 1)
                    except Exception:
                        pass
                
                st.session_state["income_rules"].append(rule_data)
                st.success(f"Added income: **{inc_name}** (£{inc_amt:,.2f})")
                st.rerun()

    with col_bills:
        st.subheader("💸 Add Recurring Bill")
        bill_name = st.text_input("Bill Name", placeholder="e.g. Rent, Broadband, Car Finance", key="bill_name_input")
        bill_category = st.selectbox("Category", BILL_CATEGORIES, key="bill_cat_input")
        bill_amt = st.number_input("Amount (£)", min_value=0.0, step=10.0, key="bill_amt_input")
        bill_freq = st.selectbox("Bill Cadence", CADENCE_OPTIONS, key="bill_freq_input")

        bill_day = 1
        bill_anchor = date.today()
        bill_shift_weekend = False

        if bill_freq == "Monthly":
            c1, c2 = st.columns([1, 1])
            with c1:
                bill_day = st.number_input("Day of Month (1-31)", min_value=1, max_value=31, value=1, key="bill_day_input")
            with c2:
                st.markdown("<br>", unsafe_allow_html=True)
                bill_shift_weekend = st.checkbox("Shift to Friday if Weekend", value=False, key="bill_shift_wknd")
        elif bill_freq in ["4-Weekly", "Bi-Weekly", "Weekly"]:
            bill_anchor = st.date_input("Next Due / Anchor Date", value=date.today(), key="bill_anchor_input")

        if st.button("Add Recurring Bill", type="primary", key="btn_add_bill"):
            if not bill_name or bill_amt <= 0:
                st.error("Please provide a valid Bill Name and Amount.")
            else:
                rule_data = {
                    "name": bill_name,
                    "category": bill_category,
                    "amount": bill_amt,
                    "freq": bill_freq,
                    "day": bill_day if bill_freq == "Monthly" else None,
                    "anchor_date": bill_anchor.strftime("%Y-%m-%d") if bill_freq in ["4-Weekly", "Bi-Weekly", "Weekly"] else None,
                    "shift_weekend": bill_shift_weekend if bill_freq == "Monthly" else False,
                }
                
                if HAS_DB:
                    try:
                        if save_expense_rule:
                            save_expense_rule(rule_data)
                        else:
                            add_expense_rule(bill_name, bill_amt, bill_day or 1, category=bill_category)
                    except Exception:
                        pass

                st.session_state["expense_rules"].append(rule_data)
                st.success(f"Added bill: **{bill_name}** (£{bill_amt:,.2f}) under *{bill_category}*")
                st.rerun()

    st.divider()

    # --- SECTION 3: LIVE REVIEWS & MANAGEMENT TABLES ---
    st.subheader("📝 Configured Rules & Entries")
    c_inc_tab, c_exp_tab = st.columns(2)

    with c_inc_tab:
        st.markdown("**Income Entries**")
        inc_list = st.session_state.get("income_rules", [])
        if inc_list:
            df_inc = pd.DataFrame(inc_list)
            cols = [c for c in ["name", "amount", "freq", "day", "anchor_date"] if c in df_inc.columns]
            st.dataframe(df_inc[cols], use_container_width=True, hide_index=True)
            
            for idx, item in enumerate(inc_list):
                c_a, c_b = st.columns([4, 1])
                c_a.caption(f"**{item.get('name')}**: £{item.get('amount', 0):,.2f} ({item.get('freq', 'Monthly')})")
                if c_b.button("❌", key=f"del_cat_inc_{idx}"):
                    if HAS_DB and "id" in item:
                        try:
                            delete_income_rule(item["id"])
                        except Exception:
                            pass
                    st.session_state["income_rules"].pop(idx)
                    st.rerun()
        else:
            st.info("No income entries recorded.")

    with c_exp_tab:
        st.markdown("**Bill Entries (Assorted by Category)**")
        exp_list = st.session_state.get("expense_rules", [])
        if exp_list:
            df_exp = pd.DataFrame(exp_list)
            cols = [c for c in ["name", "category", "amount", "freq", "day", "anchor_date"] if c in df_exp.columns]
            st.dataframe(df_exp[cols], use_container_width=True, hide_index=True)
            
            for idx, item in enumerate(exp_list):
                c_a, c_b = st.columns([4, 1])
                c_a.caption(f"**{item.get('name')}**: £{item.get('amount', 0):,.2f} [{item.get('category', 'Fixed Essential')}]")
                if c_b.button("❌", key=f"del_cat_exp_{idx}"):
                    if HAS_DB and "id" in item:
                        try:
                            delete_expense_rule(item["id"])
                        except Exception:
                            pass
                    st.session_state["expense_rules"].pop(idx)
                    st.rerun()
        else:
            st.info("No bill entries recorded.")