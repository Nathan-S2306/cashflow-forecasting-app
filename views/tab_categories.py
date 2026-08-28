import streamlit as st
import pandas as pd
from datetime import date


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

                if st.button("Process & Categorize Import", key="btn_proc_csv"):
                    st.info("Transactions imported and categorized successfully!")
            except Exception as ex:
                st.error(f"Error processing CSV: {ex}")

    st.divider()

    # --- SUB-SECTION 2: RECURRING BILLS & INCOME MANAGEMENT ---
    col_income, col_bills = st.columns(2)

    CADENCE_OPTIONS = [
        "Monthly",
        "4-Weekly",
        "Last Working Day",
        "Last Friday",
        "Bi-Weekly",
        "Weekly"
    ]

    with col_income:
        st.subheader("💰 Income Sources")
        inc_name = st.text_input("Income Name", value="", placeholder="e.g. Main Salary", key="inc_name_input")
        inc_amt = st.number_input("Amount (£)", value=0.0, step=50.0, key="inc_amt_input")
        inc_freq = st.selectbox("Pay Cadence", CADENCE_OPTIONS, key="inc_freq_input")

        # Dynamic parameter capture
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
            if not inc_name:
                st.error("Please provide an Income Name.")
            else:
                inc_rule = {
                    "name": inc_name,
                    "amount": inc_amt,
                    "freq": inc_freq,
                    "day": inc_day if inc_freq == "Monthly" else None,
                    "anchor_date": inc_anchor.strftime("%Y-%m-%d") if inc_freq in ["4-Weekly", "Bi-Weekly", "Weekly"] else None,
                    "shift_weekend": inc_shift_weekend if inc_freq == "Monthly" else False,
                }
                st.success(f"Added income rule: **{inc_name}** ({inc_freq} - £{inc_amt:,.2f})")

    with col_bills:
        st.subheader("💸 Recurring Bills & Subscriptions")
        bill_name = st.text_input("Bill Name", value="", placeholder="e.g. Rent, Broadband", key="bill_name_input")
        bill_amt = st.number_input("Amount (£)", value=0.0, step=10.0, key="bill_amt_input")
        bill_freq = st.selectbox("Bill Cadence", CADENCE_OPTIONS, key="bill_freq_input")

        # Dynamic parameter capture
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
            if not bill_name:
                st.error("Please provide a Bill Name.")
            else:
                bill_rule = {
                    "name": bill_name,
                    "amount": bill_amt,
                    "freq": bill_freq,
                    "day": bill_day if bill_freq == "Monthly" else None,
                    "anchor_date": bill_anchor.strftime("%Y-%m-%d") if bill_freq in ["4-Weekly", "Bi-Weekly", "Weekly"] else None,
                    "shift_weekend": bill_shift_weekend if bill_freq == "Monthly" else False,
                }
                st.success(f"Added bill rule: **{bill_name}** ({bill_freq} - £{bill_amt:,.2f})")