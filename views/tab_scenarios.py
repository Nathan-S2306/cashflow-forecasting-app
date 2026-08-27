import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from views.tab_overview import calculate_cashflow_timeline


def render_scenarios_tab():
    st.header("🧪 What-If Planning & Risk Analysis")
    st.caption("Simulate salary adjustments, inflation changes, and run Monte Carlo cashflow simulations.")

    tab_sandbox, tab_mc = st.tabs(["🎛️ What-If Sandbox", "🎲 Monte Carlo Risk Simulator"])

    with tab_sandbox:
        col_ctrl, col_chart = st.columns([1, 2])

        with col_ctrl:
            st.subheader("Simulation Adjustments")
            base_bal = st.number_input("Base Starting Balance (£)", value=1500.0, step=50.0, key="sc_base_bal")
            salary_mod = st.slider("Income Adjustment (%)", -30, 30, 0, step=5, key="sc_sal_mod")
            bill_mod = st.slider("Bill Inflation (%)", 0, 30, 0, step=1, key="sc_bill_mod")
            one_off_cost = st.number_input("Unexpected One-Off Cost (£)", value=0.0, step=50.0, key="sc_one_off")

        with col_chart:
            df_base = calculate_cashflow_timeline(base_bal, days=90)
            df_sim = df_base.copy()

            df_sim["Net_Change"] = df_sim["Net_Change"].apply(
                lambda x: x * (1 + salary_mod / 100.0) if x > 0 else x * (1 + bill_mod / 100.0)
            )
            if one_off_cost > 0 and len(df_sim) > 15:
                df_sim.loc[15, "Net_Change"] -= one_off_cost

            df_sim["Balance"] = base_bal + df_sim["Net_Change"].cumsum()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_base["Date"], y=df_base["Balance"], name="Baseline Forecast", line=dict(dash="dash", color="gray")))
            fig.add_trace(go.Scatter(x=df_sim["Date"], y=df_sim["Balance"], name="Simulated Scenario", line=dict(color="#1f77b4", width=3)))
            fig.update_layout(title="Baseline vs. What-If Scenario", margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

    with tab_mc:
        st.subheader("Monte Carlo Uncertainty Simulation")
        st.caption("Simulates prospective cashflow outcomes incorporating random daily variances.")

        col_m1, col_m2 = st.columns([1, 2])

        with col_m1:
            num_sims = st.slider("Number of Simulations", 50, 500, 250, step=50, key="mc_num_sims")
            std_dev = st.slider("Daily Volatility (£)", 5.0, 100.0, 25.0, step=5.0, key="mc_volatility")
            sim_days = st.slider("Simulation Window (Days)", 30, 180, 90, key="mc_sim_days")

        with col_m2:
            base_df = calculate_cashflow_timeline(base_bal, days=sim_days)
            daily_nets = base_df["Net_Change"].values

            sim_matrix = np.zeros((num_sims, sim_days))
            for s in range(num_sims):
                noise = np.random.normal(0, std_dev, sim_days)
                sim_matrix[s, :] = base_bal + np.cumsum(daily_nets + noise)

            df_mc = pd.DataFrame({
                "Date": base_df["Date"],
                "Worst Case (10th)": np.percentile(sim_matrix, 10, axis=0),
                "Expected (50th)": np.percentile(sim_matrix, 50, axis=0),
                "Best Case (90th)": np.percentile(sim_matrix, 90, axis=0),
            })

            fig_mc = go.Figure()
            fig_mc.add_trace(go.Scatter(x=df_mc["Date"], y=df_mc["Best Case (90th)"], name="Best Case (90th %ile)", line=dict(color="green", dash="dot")))
            fig_mc.add_trace(go.Scatter(x=df_mc["Date"], y=df_mc["Expected (50th)"], name="Expected Baseline", line=dict(color="blue", width=2)))
            fig_mc.add_trace(go.Scatter(x=df_mc["Date"], y=df_mc["Worst Case (10th)"], name="Worst Case (10th %ile)", line=dict(color="red", dash="dot")))
            fig_mc.update_layout(title="Monte Carlo Confidence Bands", margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified")
            st.plotly_chart(fig_mc, use_container_width=True)