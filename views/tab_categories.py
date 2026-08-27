import pandas as pd
import plotly.express as px
import streamlit as st
from core.db import load_expense_rules, load_planned_purchases


def render_categories_tab():
    st.header("🏷️ Where Money Goes & Category Analysis")
    st.caption("Visual breakdown of recurring monthly commitments and upcoming large one-off purchases.")

    expenses = load_expense_rules()
    purchases = load_planned_purchases()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Spending by Category")
        if expenses:
            exp_data = [{"Name": e[1], "Amount": e[2], "Category": e[5] if len(e) > 5 else "General"} for e in expenses]
            df_exp = pd.DataFrame(exp_data)
            df_cat = df_exp.groupby("Category")["Amount"].sum().reset_index()

            fig_donut = px.pie(
                df_cat, values="Amount", names="Category", hole=0.4,
                title="Monthly Expense Distribution", color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            st.dataframe(df_exp[["Name", "Category", "Amount"]], use_container_width=True, hide_index=True)
        else:
            st.info("No regular expenses logged yet.")

    with col2:
        st.subheader("Upcoming Planned Purchases Timeline")
        if purchases:
            pur_data = [{"Item": p[1], "Amount": p[2], "Date": p[3], "Category": p[4] if len(p) > 4 else "General"} for p in purchases]
            df_pur = pd.DataFrame(pur_data)
            df_pur["Date"] = pd.to_datetime(df_pur["Date"])
            df_pur = df_pur.sort_values("Date")

            fig_bar = px.bar(
                df_pur, x="Date", y="Amount", color="Category", hover_name="Item",
                title="Planned Purchase Schedule", color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            st.dataframe(df_pur[["Item", "Date", "Category", "Amount"]], use_container_width=True, hide_index=True)
        else:
            st.info("No one-off purchases scheduled yet.")