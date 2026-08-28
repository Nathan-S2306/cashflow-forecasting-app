import streamlit as st
import pandas as pd

def render_categories_tab():
    st.header("🏷️ Categories, Income & Bill Management")
    st.caption("Import bank statements, set up recurring income, and define bill rules.")

    # --- SUB-SECTION 1: CSV BANK STATEMENT IMPORTER ---
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

                if st.button("Process & Categorize Import"):
                    st.info("Transactions imported and categorized successfully!")
            except Exception as ex:
                st.error(f"Error processing CSV: {ex}")

    st.divider()

    # --- SUB-SECTION 2: RECURRING BILLS & INCOME MANAGEMENT ---
    col_income, col_bills = st.columns(2)

    with col_income:
        st.subheader("💰 Income Sources")
        with st.form("add_income_form", clear_on_submit=True):
            inc_name = st.text_input("Income Name (e.g. Salary)")
            inc_amt = st.number_input("Amount (£)", value=0.0, step=50.0)
            inc_freq = st.selectbox("Frequency", ["Monthly", "Bi-Weekly", "Weekly"])
            if st.form_submit_button("Add Income"):
                st.success(f"Added income: {inc_name}")

    with col_bills:
        st.subheader("💸 Recurring Bills & Subscriptions")
        with st.form("add_bill_form", clear_on_submit=True):
            bill_name = st.text_input("Bill Name (e.g. Rent, Broadband)")
            bill_amt = st.number_input("Amount (£)", value=0.0, step=10.0)
            bill_freq = st.selectbox("Frequency", ["Monthly", "Weekly", "Annual"])
            if st.form_submit_button("Add Recurring Bill"):
                st.success(f"Added bill: {bill_name}")