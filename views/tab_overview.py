from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from core.db import (
    add_expense_rule,
    add_income_rule,
    add_planned_purchase,
    delete_expense_rule,
    delete_income_rule,
    delete_planned_purchase,
    load_expense_rules,
    load_income_rules,
    load_planned_purchases,
)


def calculate_cashflow_timeline(start_balance: float, days: int = 90) -> pd.DataFrame:
    start_date = pd.Timestamp(datetime.today().date())
    date_range = pd.date_range(start=start_date, periods=days, freq="D")

    incomes = load_income_rules()
    expenses = load_expense_rules()
    purchases = load_planned_purchases()

    df = pd.DataFrame({"Date": date_range})
    df["Date_Str"] = df["Date"].dt.strftime("%Y-%m-%d")
    df["Day"] = df["Date"].dt.day
    df["Net_Change"] = 0.0

    net_changes = pd.Series(0.0, index=df["Date_Str"])

    for d in date_range:
        d_str = d.strftime("%Y-%m-%d")
        day_num = d.day

        inc_total = sum(inc[2] for inc in incomes if inc[3] == day_num)
        exp_total = sum(exp[2] for exp in expenses if exp[3] == day_num)
        pur_total = sum(pur[2] for pur in purchases if pur[3] == d_str)

        net_changes[d_str] += (inc_total - exp_total - pur_total)

    df["Net_Change"] = df["Date_Str"].map(net_changes).fillna(0.0)
    df["Balance"] = start_balance + df["Net_Change"].cumsum()
    return df


def aggregate_timeline_data(df: pd.DataFrame, view_mode: str) -> pd.DataFrame:
    df_agg = df.copy()
    if view_mode == "Weekly":
        df_agg = df_agg.resample("W-MON", on="Date").agg({"Balance": "last", "Net_Change": "sum"}).reset_index()
    elif view_mode == "Monthly":
        df_agg = df_agg.resample("ME", on="Date").agg({"Balance": "last", "Net_Change": "sum"}).reset_index()
    elif view_mode == "Yearly":
        df_agg = df_agg.resample("YE", on="Date").agg({"Balance": "last", "Net_Change": "sum"}).reset_index()
    return df_agg


def render_overview_tab():
    st.header("📊 Cashflow & Money Summary")

    col_s1, col_s2 = st.columns([1, 3])
    with col_s1:
        start_balance = st.number_input("Current Starting Balance (£)", value=1500.0, step=50.0, key="ov_start_bal")
        cushion_limit = st.number_input("Safety Cushion Limit (£)", value=300.0, step=50.0, key="ov_cushion")
        horizon_days = st.slider("Forecast Horizon (Days)", 30, 730, 90, key="ov_horizon")

    df_cf = calculate_cashflow_timeline(start_balance, horizon_days)

    final_bal = df_cf["Balance"].iloc[-1]
    lowest_bal = df_cf["Balance"].min()
    lowest_date = df_cf.loc[df_cf["Balance"].idxmin(), "Date_Str"]

    with col_s2:
        m1, m2, m3 = st.columns(3)
        m1.metric("Final Balance", f"£{final_bal:,.2f}")
        m2.metric("Lowest Balance Point", f"£{lowest_bal:,.2f}")
        m3.metric("Lowest Point Date", lowest_date)

        if lowest_bal < cushion_limit:
            st.error(f"⚠️ **Safety Alert:** Balance drops below your £{cushion_limit:,.2f} cushion on **{lowest_date}** (Lowest point: £{lowest_bal:,.2f}).")
        else:
            st.success(f"✅ Forecast stays safely above your £{cushion_limit:,.2f} cushion.")

    st.markdown("---")
    col_v1, col_v2 = st.columns([3, 1])
    with col_v1:
        st.subheader("Account Balance Projection")
    with col_v2:
        view_mode = st.radio("View Interval", ["Daily", "Weekly", "Monthly", "Yearly"], horizontal=True, key="ov_view_mode")

    df_chart = aggregate_timeline_data(df_cf, view_mode)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_chart["Date"],
        y=df_chart["Balance"],
        mode="lines+markers" if view_mode != "Daily" else "lines",
        name="Projected Balance",
        line=dict(color="#1f77b4", width=2.5)
    ))

    # Soft red warning region below cushion threshold
    fig.add_hrect(
        y0=0, y1=cushion_limit,
        fillcolor="rgba(255, 0, 0, 0.12)", line_width=0,
        annotation_text="Safety Threshold Warning", annotation_position="bottom right"
    )

    fig.add_hline(y=cushion_limit, line_dash="dash", line_color="red")
    fig.update_layout(xaxis_title="Date", yaxis_title="Balance (£)", hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("⚙️ Manage Monthly Income, Bills & One-Off Spends")

    col_inc, col_exp, col_pur = st.columns(3)

    with col_inc:
        st.markdown("### 💵 Money In (Income)")
        for inc in load_income_rules():
            c_a, c_b = st.columns([3, 1])
            c_a.write(f"**{inc[1]}**: £{inc[2]:,.2f} (Day {inc[3]})")
            if c_b.button("❌", key=f"del_inc_{inc[0]}"):
                delete_income_rule(inc[0])
                st.rerun()

        with st.expander("➕ Add Income"):
            i_name = st.text_input("Source Name", key="add_inc_name")
            i_amt = st.number_input("Amount (£)", min_value=0.0, step=10.0, key="add_inc_amt")
            i_day = st.number_input("Day of Month (1-31)", min_value=1, max_value=31, value=1, key="add_inc_day")
            if st.button("Save Income", key="btn_save_inc"):
                if i_name and i_amt > 0:
                    add_income_rule(i_name, i_amt, i_day)
                    st.success("Income added!")
                    st.rerun()

    with col_exp:
        st.markdown("### 💸 Regular Bills")
        for exp in load_expense_rules():
            c_a, c_b = st.columns([3, 1])
            cat_label = exp[5] if len(exp) > 5 else "General"
            c_a.write(f"**{exp[1]}**: £{exp[2]:,.2f} (Day {exp[3]}) [{cat_label}]")
            if c_b.button("❌", key=f"del_exp_{exp[0]}"):
                delete_expense_rule(exp[0])
                st.rerun()

        with st.expander("➕ Add Bill"):
            e_name = st.text_input("Bill Name", key="add_exp_name")
            e_amt = st.number_input("Amount (£)", min_value=0.0, step=10.0, key="add_exp_amt")
            e_day = st.number_input("Day of Month (1-31)", min_value=1, max_value=31, value=1, key="add_exp_day")
            e_cat = st.selectbox("Category", ["Housing", "Bills", "Living Expenses", "Fun", "General"], key="add_exp_cat")
            if st.button("Save Bill", key="btn_save_exp"):
                if e_name and e_amt > 0:
                    add_expense_rule(e_name, e_amt, e_day, category=e_cat)
                    st.success("Bill added!")
                    st.rerun()

    with col_pur:
        st.markdown("### 🛍️ One-Off Spends")
        for pur in load_planned_purchases():
            c_a, c_b = st.columns([3, 1])
            c_a.write(f"**{pur[1]}**: £{pur[2]:,.2f} on {pur[3]}")
            if c_b.button("❌", key=f"del_pur_{pur[0]}"):
                delete_planned_purchase(pur[0])
                st.rerun()

        with st.expander("➕ Add One-Off Spend"):
            p_name = st.text_input("Item Name", key="add_pur_name")
            p_amt = st.number_input("Amount (£)", min_value=0.0, step=10.0, key="add_pur_amt")
            p_date = st.date_input("Target Date", key="add_pur_date").strftime("%Y-%m-%d")
            p_cat = st.selectbox("Category", ["Housing", "Bills", "Living Expenses", "Fun", "General"], key="add_pur_cat")
            if st.button("Save Purchase", key="btn_save_pur"):
                if p_name and p_amt > 0:
                    add_planned_purchase(p_name, p_amt, p_date, category=p_cat)
                    st.success("Purchase added!")
                    st.rerun()