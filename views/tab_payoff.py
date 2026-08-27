import pandas as pd
import streamlit as st
from core.db import add_debt, add_savings_goal, delete_debt, delete_savings_goal, load_debts, load_savings_goals


def render_payoff_tab():
    st.header("🎯 Debts & Savings Goals")
    st.caption("Track priority debt payoff plans and monitor progress toward long-term savings targets.")

    tab_debt, tab_savings = st.tabs(["💳 Priority Debt Payoff", "🐷 Savings Goals Progress"])

    with tab_debt:
        st.subheader("StepChange Debt Management Strategy")
        debts = load_debts()

        col_left, col_right = st.columns([3, 2])

        with col_left:
            if debts:
                df_debts = pd.DataFrame(debts, columns=["ID", "Name", "Balance", "Interest_Rate", "Min_Payment", "Is_Priority"])
                strategy = st.radio("Payoff Strategy Order", ["StepChange Priority Rules", "Avalanche (Highest APR First)", "Snowball (Lowest Balance First)"], horizontal=True)

                if strategy == "StepChange Priority Rules":
                    df_debts = df_debts.sort_values(by=["Is_Priority", "Interest_Rate"], ascending=[False, False])
                elif strategy == "Avalanche (Highest APR First)":
                    df_debts = df_debts.sort_values(by="Interest_Rate", ascending=False)
                else:
                    df_debts = df_debts.sort_values(by="Balance", ascending=True)

                for _, row in df_debts.iterrows():
                    prio_badge = "🔴 [MUST PAY FIRST - PRIORITY]" if row["Is_Priority"] == 1 else "🔵 [Non-Priority]"
                    with st.container():
                        st.markdown(f"#### {row['Name']} {prio_badge}")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Balance", f"£{row['Balance']:,.2f}")
                        c2.metric("Interest Rate", f"{row['Interest_Rate']:.1f}%")
                        c3.metric("Min Payment", f"£{row['Min_Payment']:,.2f}")
                        if c4.button("Clear / Delete", key=f"del_debt_{int(row['ID'])}"):
                            delete_debt(int(row["ID"]))
                            st.rerun()
                        st.divider()
            else:
                st.info("No debts listed.")

        with col_right:
            with st.expander("➕ Add Debt Account", expanded=True):
                d_name = st.text_input("Account Name (e.g., Council Tax Arrears, Credit Card)")
                d_bal = st.number_input("Current Balance (£)", min_value=0.0, step=50.0)
                d_rate = st.number_input("Interest Rate (APR %)", min_value=0.0, step=0.1)
                d_min = st.number_input("Minimum Monthly Payment (£)", min_value=0.0, step=5.0)
                d_prio = st.checkbox("Priority Debt (e.g., Rent, Council Tax, Gas/Electric Arrears)")

                if st.button("Save Debt Account"):
                    if d_name and d_bal > 0:
                        add_debt(d_name, d_bal, d_rate, d_min, 1 if d_prio else 0)
                        st.success("Debt added!")
                        st.rerun()

    with tab_savings:
        st.subheader("Savings Goals & Pot Targets")
        goals = load_savings_goals()

        col_g1, col_g2 = st.columns([3, 2])

        with col_g1:
            if goals:
                for goal in goals:
                    g_id, g_name, g_target, g_curr, g_date, g_contrib = goal
                    pct = min(100.0, (g_curr / g_target) * 100) if g_target > 0 else 0.0

                    st.markdown(f"#### {g_name}")
                    st.progress(pct / 100.0)
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Target", f"£{g_target:,.2f}")
                    m2.metric("Saved So Far", f"£{g_curr:,.2f}")
                    m3.metric("Target Date", g_date)
                    if m4.button("Delete Goal", key=f"del_goal_{g_id}"):
                        delete_savings_goal(g_id)
                        st.rerun()
                    st.divider()
            else:
                st.info("No active savings goals.")

        with col_g2:
            with st.expander("➕ Add Savings Goal", expanded=True):
                s_name = st.text_input("Goal Name (e.g., Emergency Fund)")
                s_target = st.number_input("Target Amount (£)", min_value=10.0, step=50.0)
                s_curr = st.number_input("Current Amount Saved (£)", min_value=0.0, step=10.0)
                s_date = st.date_input("Target Completion Date").strftime("%Y-%m-%d")
                s_contrib = st.number_input("Monthly Contribution (£)", min_value=0.0, step=10.0)

                if st.button("Save Savings Goal"):
                    if s_name and s_target > 0:
                        add_savings_goal(s_name, s_target, s_curr, s_date, s_contrib)
                        st.success("Savings goal saved!")
                        st.rerun()