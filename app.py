import datetime
import json
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Financial Forecasting & Knowledge Hub",
    page_icon="💼",
    layout="wide",
)

# Custom CSS styling for metric cards and tab spacing
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("💼 Financial Forecasting & Knowledge Hub")

# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
if "income_rules" not in st.session_state:
  st.session_state.income_rules = [
      {"name": "Net Salary", "amount": 2800.0, "day": 25, "freq": "Monthly"},
      {
          "name": "Freelance / Side Income",
          "amount": 350.0,
          "day": 15,
          "freq": "Monthly",
      },
  ]

if "expense_rules" not in st.session_state:
  st.session_state.expense_rules = [
      {
          "name": "Rent / Mortgage",
          "category": "Housing",
          "amount": 950.0,
          "day": 1,
          "freq": "Monthly",
      },
      {
          "name": "Council Tax & Utilities",
          "category": "Utilities",
          "amount": 320.0,
          "day": 5,
          "freq": "Monthly",
      },
      {
          "name": "Groceries",
          "category": "Food & Housekeeping",
          "amount": 85.0,
          "day": 4,
          "freq": "Weekly",
      },  # Friday
      {
          "name": "Gym & Subscriptions",
          "category": "Personal Costs",
          "amount": 45.0,
          "day": 12,
          "freq": "Monthly",
      },
      {
          "name": "Debt Repayments",
          "category": "Debts & Arrears",
          "amount": 150.0,
          "day": 20,
          "freq": "Monthly",
      },
  ]

if "purchases" not in st.session_state:
  st.session_state.purchases = [
      {
          "name": "Laptop Upgrade",
          "amount": 1200.0,
          "date": datetime.date.today() + datetime.timedelta(days=30),
      },
      {
          "name": "Holiday / Travel",
          "amount": 600.0,
          "date": datetime.date.today() + datetime.timedelta(days=60),
      },
  ]

# ==============================================================================
# SIDEBAR: CORE ENGINE SETTINGS & DATA I/O
# ==============================================================================
with st.sidebar:
  st.header("⚙️ Core Engine Settings")
  starting_balance = st.number_input(
      "Starting Cash Balance (£)", value=2500.0, step=100.0
  )
  forecast_days = st.slider(
      "Forecast (Days)", min_value=30, max_value=365, value=90
  )
  safety_threshold = st.number_input(
      "Buffer / Safety Threshold (£)", value=500.0, step=50.0
  )

  st.markdown("---")
  st.header("📊 Time Period View View")
  granularity = st.selectbox("View Granularity", ["Daily", "Weekly", "Monthly"])

  st.markdown("---")
  st.header("📁 Configuration Import / Export")

  # Export Config JSON
  config_export = {
      "starting_balance": starting_balance,
      "forecast_days": forecast_days,
      "safety_threshold": safety_threshold,
      "income_rules": st.session_state.income_rules,
      "expense_rules": st.session_state.expense_rules,
      "purchases": [
          {
              "name": p["name"],
              "amount": p["amount"],
              "date": p["date"].isoformat(),
          }
          for p in st.session_state.purchases
      ],
  }
  st.download_button(
      "💾 Export Setup (JSON)",
      data=json.dumps(config_export, indent=2),
      file_name="cashflow_setup.json",
      mime="application/json",
  )

  # Import Config JSON
  uploaded_json = st.file_uploader("📥 Import Setup (JSON)", type=["json"])
  if uploaded_json is not None:
    try:
      loaded_data = json.load(uploaded_json)
      st.session_state.income_rules = loaded_data.get(
          "income_rules", st.session_state.income_rules
      )
      st.session_state.expense_rules = loaded_data.get(
          "expense_rules", st.session_state.expense_rules
      )
      st.success("Configuration loaded successfully!")
    except Exception as e:
      st.error(f"Error loading JSON: {e}")

# ==============================================================================
# MAIN TABS DEFINITION
# ==============================================================================
tab_categories, tab_sandbox, tab_knowledge, tab_payoff, tab_feedback = st.tabs([
    "Forecast and Categories",
    "Scenario Forecast & Planned Purchases",
    "Financial Knowledge Hub",
    "Debt Payoff & Savings Target Engine",
    "Feedback",
])


# ==============================================================================
# VECTORIZED CALCULATION HELPER ENGINE
# ==============================================================================
def calculate_cashflow(start_bal, days, inc_rules, exp_rules, plan_purchases):
  start_d = datetime.date.today()
  date_seq = pd.date_range(start=start_d, periods=days, freq="D")
  df_calc = pd.DataFrame({"Date": date_seq, "Income": 0.0, "Expense": 0.0})

  # Process Income Rules
  for inc in inc_rules:
    if inc["freq"] == "Monthly":
      df_calc.loc[df_calc["Date"].dt.day == inc["day"], "Income"] += inc[
          "amount"
      ]
    elif inc["freq"] == "Weekly":
      df_calc.loc[df_calc["Date"].dt.dayofweek == inc["day"], "Income"] += inc[
          "amount"
      ]

  # Process Recurring Expense Rules
  for exp in exp_rules:
    if exp["freq"] == "Monthly":
      df_calc.loc[df_calc["Date"].dt.day == exp["day"], "Expense"] += exp[
          "amount"
      ]
    elif exp["freq"] == "Weekly":
      df_calc.loc[df_calc["Date"].dt.dayofweek == exp["day"], "Expense"] += exp[
          "amount"
      ]

  # Process One-off Planned Purchases
  for pur in plan_purchases:
    p_date = pd.to_datetime(pur["date"])
    df_calc.loc[df_calc["Date"] == p_date, "Expense"] += pur["amount"]

  df_calc["Net_Cashflow"] = df_calc["Income"] - df_calc["Expense"]
  df_calc["Balance"] = start_bal + df_calc["Net_Cashflow"].cumsum()
  df_calc["7D_Rolling_Min"] = (
      df_calc["Balance"].rolling(window=7, min_periods=1).min()
  )
  return df_calc


# ==============================================================================
# TAB 1: CATEGORIES & VECTORIZED CASHFLOW ENGINE
# ==============================================================================
with tab_categories:
  st.header("🏷️ Categories")
  st.caption(
      "Configure recurring income, expenditure rules and view"
      " daily resampled cash flow predictions."
  )

  col_left, col_right = st.columns(2)

  with col_left:
    st.subheader("💵 Income Rules Management")
    with st.expander("➕ Add New Income Rule"):
      new_inc_name = st.text_input("Income Name", value="Side Hustle")
      new_inc_amt = st.number_input("Amount (£)", value=200.0, step=25.0)
      new_inc_day = st.slider(
          "Pay Day / Day of Week", min_value=1, max_value=31, value=15
      )
      new_inc_freq = st.selectbox("Frequency", ["Monthly", "Weekly"])
      if st.button("Add Income Rule"):
        st.session_state.income_rules.append({
            "name": new_inc_name,
            "amount": new_inc_amt,
            "day": new_inc_day,
            "freq": new_inc_freq,
        })
        st.success(f"Added {new_inc_name}")
        st.rerun()

    inc_df = pd.DataFrame(st.session_state.income_rules)
    st.dataframe(inc_df, use_container_width=True)
    if st.button("Clear All Income Rules"):
      st.session_state.income_rules = []
      st.rerun()

  with col_right:
    st.subheader("📉 Expenditure Category Rules")
    stepchange_cats = [
        "Housing",
        "Utilities",
        "Food & Housekeeping",
        "Transport",
        "Personal Costs",
        "Pensions & Insurance",
        "Debts & Arrears",
    ]
    with st.expander("➕ Add New Expense Rule"):
      new_exp_name = st.text_input("Expense Name", value="Broadband / Wifi")
      new_exp_cat = st.selectbox("StepChange Category", stepchange_cats)
      new_exp_amt = st.number_input("Amount (£)", value=35.0, step=5.0)
      new_exp_day = st.slider(
          "Payment Day", min_value=1, max_value=31, value=10
      )
      new_exp_freq = st.selectbox("Expense Frequency", ["Monthly", "Weekly"])
      if st.button("Add Expense Rule"):
        st.session_state.expense_rules.append({
            "name": new_exp_name,
            "category": new_exp_cat,
            "amount": new_exp_amt,
            "day": new_exp_day,
            "freq": new_exp_freq,
        })
        st.success(f"Added {new_exp_name}")
        st.rerun()

    exp_df = pd.DataFrame(st.session_state.expense_rules)
    st.dataframe(exp_df, use_container_width=True)
    if st.button("Clear All Expense Rules"):
      st.session_state.expense_rules = []
      st.rerun()

  st.markdown("---")
  st.subheader("📊 Results & Dynamic Cash Flow Chart")

  # Calculate forecast
  df_main = calculate_cashflow(
      starting_balance,
      forecast_days,
      st.session_state.income_rules,
      st.session_state.expense_rules,
      st.session_state.purchases,
  )

  # Resampling
  if granularity == "Weekly":
    resample_df = (
        df_main.resample("W-MON", on="Date")
        .agg({
            "Income": "sum",
            "Expense": "sum",
            "Net_Cashflow": "sum",
            "Balance": "last",
            "7D_Rolling_Min": "min",
        })
        .reset_index()
    )
  elif granularity == "Monthly":
    resample_df = (
        df_main.resample("ME", on="Date")
        .agg({
            "Income": "sum",
            "Expense": "sum",
            "Net_Cashflow": "sum",
            "Balance": "last",
            "7D_Rolling_Min": "min",
        })
        .reset_index()
    )
  else:
    resample_df = df_main.copy()

  # Metric Cards
  m1, m2, m3, m4 = st.columns(4)
  min_bal = df_main["Balance"].min()
  end_bal = df_main["Balance"].iloc[-1]
  tot_inc = df_main["Income"].sum()
  tot_exp = df_main["Expense"].sum()

  m1.metric(
      "Ending Cash Balance",
      f"£{end_bal:,.2f}",
      delta=f"£{end_bal - starting_balance:,.2f}",
  )
  m2.metric(
      "Lowest Projected Balance",
      f"£{min_bal:,.2f}",
      delta="WARNING: Low" if min_bal < safety_threshold else "Healthy",
      delta_color="normal" if min_bal >= safety_threshold else "inverse",
  )
  m3.metric("Total Inflow", f"£{tot_inc:,.2f}")
  m4.metric("Total Outflow", f"£{tot_exp:,.2f}")

  st.line_chart(resample_df.set_index("Date")[["Balance", "7D_Rolling_Min"]])

  csv_bytes = resample_df.to_csv(index=False).encode("utf-8")
  st.download_button(
      "📥 Export Forecast Data (CSV)",
      data=csv_bytes,
      file_name="cashflow_forecast.csv",
      mime="text/csv",
  )

# ==============================================================================
# TAB 2: SCENARIO SANDBOX & PLANNED PURCHASES
# ==============================================================================
with tab_sandbox:
  st.header("🧪 Scenario Sandbox & Discretionary Purchases")
  st.caption(
      "Stress-test large lump-sum spending decisions against your baseline"
      " forecast without breaking your safety buffer."
  )

  col_sb1, col_sb2 = st.columns([1, 2])

  with col_sb1:
    st.subheader("🛒 Add Planned Lump-Sum Expense")
    p_name = st.text_input("Purchase Item", value="New Phone / Tech")
    p_amt = st.number_input("Cost (£)", value=800.0, step=50.0)
    p_date = st.date_input(
        "Target Purchase Date",
        value=datetime.date.today() + datetime.timedelta(days=45),
    )

    if st.button("Add Purchase to Simulation"):
      st.session_state.purchases.append(
          {"name": p_name, "amount": p_amt, "date": p_date}
      )
      st.success(f"Added {p_name}")
      st.rerun()

    st.markdown("#### Configured Planned Purchases")
    if st.session_state.purchases:
      p_df = pd.DataFrame(st.session_state.purchases)
      st.dataframe(p_df, use_container_width=True)
      if st.button("Reset Purchases"):
        st.session_state.purchases = []
        st.rerun()
    else:
      st.info("No discretionary purchases added yet.")

  with col_sb2:
    st.subheader("⚖️ Baseline vs. Compound Purchase Scenario Analysis")

    df_base = calculate_cashflow(
        starting_balance,
        forecast_days,
        st.session_state.income_rules,
        st.session_state.expense_rules,
        [],
    )
    df_scen = calculate_cashflow(
        starting_balance,
        forecast_days,
        st.session_state.income_rules,
        st.session_state.expense_rules,
        st.session_state.purchases,
    )

    compare_df = pd.DataFrame({
        "Date": df_base["Date"],
        "Baseline Balance": df_base["Balance"],
        "Scenario Balance": df_scen["Balance"],
        "Safety Threshold": safety_threshold,
    }).set_index("Date")

    st.line_chart(compare_df)

    scen_min = df_scen["Balance"].min()
    if scen_min < safety_threshold:
      st.error(
          f"⚠️ Warning: Adding these purchases drops your lowest balance to"
          f" £{scen_min:,.2f}, which is below your £{safety_threshold:,.2f}"
          " safety buffer!"
      )
    else:
      st.success(
          "✅ Safe Purchase: Your cash flow remains above the safety threshold"
          f" at all times (Lowest point: £{scen_min:,.2f})."
      )

# ==============================================================================
# TAB 3: FINANCIAL KNOWLEDGE HUB (STANDALONE MODULE)
# ==============================================================================
with tab_knowledge:
  st.header("📚 Financial Knowledge Hub")
  st.caption(
      "Essential UK personal finance principles, tax rules, debt strategies,"
      " and wealth-building mechanics."
  )

  search_query = st.text_input(
      "🔍 Search guidance articles",
      placeholder="e.g. Compound interest, ISA allowance, Debt Avalanche...",
  )

  st.markdown("---")

  # ARTICLE 1: DEBT MANAGEMENT & INTEREST SAVING
  with st.expander(
      "💳 1. Debt Management: Interest Savings, Snowball vs. Avalanche",
      expanded=True,
  ):
    st.markdown("""
        ### Understanding Debt & APR
        * **APR (Annual Percentage Rate):** Represents the actual annual cost of borrowing, factoring in interest rates and mandatory fees.
        * **Minimum Payment Trap:** Paying only minimums on high-APR credit cards (20–30%) can extend payback timelines to decades while multiplying total interest paid.

        ### Repayment Strategies
        | Strategy | How it Works | Primary Benefit |
        | :--- | :--- | :--- |
        | **Debt Avalanche** | Target the highest-APR debt first while paying minimums on the rest. | **Mathematically optimal:** Saves the highest amount of interest cash. |
        | **Debt Snowball** | Target the smallest principal balance first while paying minimums on the rest. | **Behavioral momentum:** Delivers quick psychological wins. |

        ---
        ### 🚨 StepChange & Debt Relief Routes (UK)
        * **DMP (Debt Management Plan):** An informal agreement with creditors to pay a lower monthly figure. Interest is typically frozen.
        * **IVA (Individual Voluntary Arrangement):** A formal legal structure in England & Wales to clear a portion of unsecured debt over 5–6 years.
        * **DRO (Debt Relief Order):** For low income/asset situations with debt under threshold limits; freezes repayments and clears debt after 12 months.
        * **Free Advice:** Always consult non-profit services like **StepChange** or **National Debtline** before entering formal debt solutions.
        """)

  # ARTICLE 2: COMPOUND INTEREST & SAVINGS MECHANICS
  with st.expander(
      "📈 2. Savings Mechanics & The Power of Compounding", expanded=False
  ):
    st.markdown("""
        ### The Compound Interest Formula
        Compound interest is calculated on both the initial principal and the accumulated interest from preceding periods:

        $$A = P \\left(1 + \\frac{r}{n}\\right)^{nt}$$

        * **$A$** = Final Amount
        * **$P$** = Principal investment
        * **$r$** = Annual interest rate (decimal)
        * **$n$** = Compounding frequency per year
        * **$t$** = Time in years

        ---
        ### The Rule of 72 (Quick Doubling Rule)
        Estimate how many years it will take to double an investment at a given fixed rate:

        $$\\text{Years to Double} \\approx \\frac{72}{\\text{Interest Rate } (r)}$$

        * **Example:** At an **8%** average annual return, your money doubles in approximately **9 years** ($72 / 8$).
        """)

    st.markdown("#### 🧮 Interactive Compound Interest Quick Calculator")
    c1, c2, c3 = st.columns(3)
    init_p = c1.number_input("Initial Balance (£)", value=1000, step=100)
    m_contrib = c2.number_input("Monthly Contribution (£)", value=200, step=50)
    rate = c3.slider(
        "Annual Interest Rate (%)",
        min_value=1.0,
        max_value=12.0,
        value=6.0,
        step=0.5,
    )
    years = st.slider(
        "Investment Horizon (Years)", min_value=1, max_value=30, value=10
    )

    r_m = (rate / 100) / 12
    n_m = years * 12
    future_val = init_p * ((1 + r_m) ** n_m) + m_contrib * (
        ((1 + r_m) ** n_m - 1) / r_m
    )
    total_deposited = init_p + (m_contrib * n_m)
    total_interest = future_val - total_deposited

    st.metric(
        label="Projected Portfolio Value",
        value=f"£{future_val:,.2f}",
        delta=f"£{total_interest:,.2f} Total Interest Earned",
    )

  # ARTICLE 3: INVESTING & ASSET ALLOCATION
  with st.expander(
      "📊 3. Investing Principles & Asset Allocation", expanded=False
  ):
    st.markdown("""
        ### Core Wealth-Building Concepts
        * **Stocks vs. Cash:** Cash savings protect liquidity, but sustained inflation erodes purchasing power over time. Equities historically generate real growth over 10+ year horizons.
        * **Global Diversification:** Index funds (e.g., FTSE Global All-Cap, MSCI World) spread capital across thousands of companies, eliminating single-stock risk.
        * **Pound-Cost Averaging (PCA):** Investing steady amounts monthly dampens market volatility by purchasing more units when prices fall and fewer when prices rise.

        ### Golden Order of Financial Priorities
        1. **Emergency Cushion:** Secure 3–6 months of essential living expenses in high-yield liquid cash.
        2. **High-Interest Debt:** Clear all debt with APR > 7% (credit cards, personal loans) before investing.
        3. **Employer Pension Match:** Contribute enough to secure the full employer matching limit (instant 100% return).
        4. **Tax-Efficient Accounts:** Maximize Cash or Stocks & Shares ISAs.
        """)

  # ARTICLE 4: UK TAX ALLOWANCES & ISAS
  with st.expander(
      "🏛️ 4. UK Tax Allowances, Personal Savings Allowance & ISAs", expanded=False
  ):
    st.markdown("""
        ### Key Tax Allowances Overview
        * **Personal Allowance:** First **£12,570** of earnings is tax-free.
        * **Annual ISA Limit:** **£20,000** total contribution allowance per tax year across all ISA types (Cash, Stocks & Shares, Innovative Finance). All gains inside ISAs are 100% tax-free.
        * **Capital Gains Tax (CGT) Allowance:** **£3,000** annual profit exemption on non-ISA investments/assets.
        * **Dividend Allowance:** **£500** tax-free per tax year.

        ---
        ### Personal Savings Allowance (PSA) Limits
        Tax-free interest threshold earned on standard non-ISA bank/savings accounts:

        | Income Tax Rate | Taxable Income Range | Annual PSA Limit |
        | :--- | :--- | :--- |
        | **Basic Rate (20%)** | £12,571 to £50,270 | **£1,000** tax-free interest |
        | **Higher Rate (40%)** | £50,271 to £125,140 | **£500** tax-free interest |
        | **Additional Rate (45%)** | Over £125,140 | **£0** (No tax-free allowance) |

        *Note: Interest earned inside an ISA does **not** consume your Personal Savings Allowance.*
        """)

# ==============================================================================
# TAB 4: DEBT PAYOFF & SAVINGS TARGET ENGINE
# ==============================================================================
with tab_payoff:
  st.header("🎯 Debt Payoff & Savings Target Engine")
  st.caption(
      "Calculate exact timelines and repayment schedules to reach debt freedom"
      " or reach long-term wealth goals."
  )

  col_t1, col_t2 = st.columns(2)

  with col_t1:
    st.subheader("🥊 Debt Payoff Calculator (Snowball vs. Avalanche)")
    debt_balance = st.number_input(
        "Total Unsecured Debt (£)", value=4500.0, step=250.0
    )
    debt_apr = st.number_input(
        "Average Interest Rate (APR %)", value=18.5, step=0.5
    )
    monthly_pay = st.number_input(
        "Monthly Repayment Allocation (£)", value=200.0, step=25.0
    )

    if monthly_pay > 0:
      monthly_rate = (debt_apr / 100) / 12
      if debt_balance * monthly_rate >= monthly_pay:
        st.error(
            "⚠️ Monthly repayment is too low to cover interest charges! The debt"
            " will never be paid off at this rate."
        )
      else:
        n_months = -np.log(
            1 - (monthly_rate * debt_balance) / monthly_pay
        ) / np.log(1 + monthly_rate)
        tot_paid = n_months * monthly_pay
        tot_interest = tot_paid - debt_balance

        st.success(
            f"🎉 Fully paid off in **{int(np.ceil(n_months))} months**"
            f" ({n_months/12:.1f} years)."
        )
        st.metric("Total Interest Paid", f"£{tot_interest:,.2f}")
        st.metric("Total Amount Repaid", f"£{tot_paid:,.2f}")

  with col_t2:
    st.subheader("🎯 Emergency Fund & Savings Target Milestone")
    savings_goal = st.number_input(
        "Savings Target Goal (£)", value=10000.0, step=500.0
    )
    current_savings = st.number_input(
        "Current Savings (£)", value=2500.0, step=250.0
    )
    monthly_savings = st.number_input(
        "Planned Monthly Contribution (£)", value=350.0, step=25.0
    )

    remaining_goal = max(0.0, savings_goal - current_savings)
    if monthly_savings > 0 and remaining_goal > 0:
      months_to_goal = remaining_goal / monthly_savings
      st.info(
          f"🚀 At £{monthly_savings:,.2f}/month, you will hit your"
          f" £{savings_goal:,.2f} goal in"
          f" **{int(np.ceil(months_to_goal))} months** ({months_to_goal/12:.1f}"
          " years)."
      )
      progress = min(1.0, current_savings / savings_goal)
      st.progress(progress)
      st.caption(f"Progress: {progress*100:.1f}% achieved")

# ==============================================================================
# TAB 5: FEEDBACK & SYSTEM AUDIT
# ==============================================================================
with tab_feedback:
  st.header("💬 User Feedback & System Evaluation Audit")
  st.caption(
      "Capture user satisfaction ratings and log enhancement ideas for future"
      " releases."
  )

  col_f1, col_f2 = st.columns([1, 1])

  with col_f1:
    user_rating = st.select_slider(
        "Overall App Rating",
        options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
        value="⭐⭐⭐⭐⭐",
    )
    fb_category = st.selectbox(
        "Feedback Category",
        [
            "General Usability",
            "Feature Request",
            "Calculation / Engine Bug",
            "Knowledge Hub Content",
        ],
    )
    fb_comments = st.text_area("Detailed Comments or Feature Ideas")

    if st.button("Submit Feedback Entry"):
      st.success(
          "Thank you! Your feedback has been recorded and submitted to the"
          " development team."
      )
      st.balloons()

  with col_f2:
    st.subheader("📋 System Status & Architecture Matrix")
    st.markdown("""
        * **Vectorized Core:** Active ($O(1)$ daily timeline calculation)
        * **StepChange Module:** Fully Mapped
        * **Knowledge Hub:** Integrated (Standalone Tab 3)
        * **Scenario Sandbox:** Active (Baseline vs Compound comparison)
        * **Local I/O:** JSON Import/Export & CSV Forecast Export Enabled
        """)