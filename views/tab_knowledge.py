import pandas as pd
import plotly.express as px
import streamlit as st


def render_knowledge_tab():
    st.header("📚 Knowledge Hub & Financial Guides")
    st.caption("Interactive projection tools alongside practical UK tax, debt strategy, and budgeting guides.")

    tab_calc, tab_debt, tab_tax, tab_foundations = st.tabs([
        "🧮 Compound Growth Calculator",
        "💳 Priority Debt & Payoff Strategies",
        "🇬🇧 UK Tax & National Insurance Guide",
        "🛡️ Financial Foundations & Budgeting",
    ])

    with tab_calc:
        st.subheader("Interactive Compound Growth Simulator")
        col_in, col_vis = st.columns([1, 2])

        with col_in:
            initial = st.number_input("Starting Balance (£)", value=1000.0, step=100.0, key="kn_ci_init")
            monthly = st.number_input("Monthly Contribution (£)", value=200.0, step=25.0, key="kn_ci_month")
            rate = st.slider("Expected Annual Return (%)", 1.0, 15.0, 7.0, step=0.5, key="kn_ci_rate") / 100
            years = st.slider("Time Horizon (Years)", 1, 40, 10, key="kn_ci_years")

        with col_vis:
            months = years * 12
            monthly_rate = rate / 12
            balance, total_deposited = initial, initial
            records = []

            for m in range(1, months + 1):
                balance = (balance + monthly) * (1 + monthly_rate)
                total_deposited += monthly
                records.append({
                    "Year": round(m / 12.0, 1),
                    "Total Pot (£)": balance,
                    "Total Contributions (£)": total_deposited
                })

            df_ci = pd.DataFrame(records)
            fig_ci = px.line(
                df_ci, x="Year", y=["Total Pot (£)", "Total Contributions (£)"],
                title="Investment Growth vs. Direct Contributions",
                color_discrete_map={"Total Pot (£)": "#1f77b4", "Total Contributions (£)": "#aec7e8"}
            )
            st.plotly_chart(fig_ci, use_container_width=True)

            m1, m2, m3 = st.columns(3)
            m1.metric("Final Pot Value", f"£{balance:,.2f}")
            m2.metric("Total Paid In", f"£{total_deposited:,.2f}")
            m3.metric("Growth Earned", f"£{balance - total_deposited:,.2f}")

    with tab_debt:
        st.subheader("Debt Prioritisation & Management Framework")
        st.markdown("""
        ### 🔴 Priority Debts (Handled First)
        Non-payment leads to severe, immediate consequences like loss of your home or legal enforcement:
        * **Mortgage & Rent Arrears**
        * **Council Tax Arrears**
        * **Gas & Electricity Bills**
        * **HMRC Tax Debt**

        ---

        ### 🔵 Non-Priority Debts (Secondary Payoff Targets)
        * **Credit Cards & Overdrafts**
        * **Personal Unsecured Loans**
        * **Buy-Now-Pay-Later (BNPL) Services**
        """)

    with tab_tax:
        st.subheader("UK Income Tax, National Insurance & Savings Thresholds")
        st.markdown("""
        * **Personal Allowance:** Up to **£12,570** (Tax-free).
        * **Basic Rate (20%):** Income from **£12,571 to £50,270**.
        * **Higher Rate (40%):** Income from **£50,271 to £125,140**.
        * **ISA Limit:** Save up to **£20,000/year** tax-free across Cash/Stocks ISAs.
        """)

    with tab_foundations:
        st.subheader("Core Financial Foundations")
        st.markdown("""
        ### 🛡️ Emergency Fund Goals
        * **Starter Cushion:** £500 to £1,000 immediately before tackling non-priority debt.
        * **Full Buffer:** 3 to 6 months of essential living costs.

        ### 📐 The 50 / 30 / 20 Rule
        * **50% Needs:** Rent/Mortgage, bills, groceries.
        * **30% Wants:** Dining, lifestyle, entertainment.
        * **20% Savings:** Investments, debt payoff, pension.
        """)