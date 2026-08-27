from datetime import date, timedelta
import numpy as np
import pandas as pd


def calculate_cashflow(starting_balance, forecast_days, income_rules, expense_rules, planned_purchases):
    """Calculates day-by-day cash balance projections."""
    start_date = date.today()
    date_range = [start_date + timedelta(days=i) for i in range(forecast_days)]

    daily_records = []
    current_balance = float(starting_balance)

    for curr_date in date_range:
        day_of_month = curr_date.day
        day_str = curr_date.strftime("%Y-%m-%d")

        # Inflows
        for inc in income_rules:
            if inc["freq"] == "Monthly" and day_of_month == inc["day"]:
                current_balance += inc["amount"]

        # Outflows
        for exp in expense_rules:
            freq = exp.get("freq", "Monthly")
            if freq == "Monthly" and day_of_month == exp["day"]:
                current_balance -= exp["amount"]
            elif freq == "Weekly" and curr_date.weekday() == 0:
                current_balance -= exp["amount"]

        # One-off spends / bonuses
        for pur in planned_purchases:
            if pur["date"] == day_str:
                current_balance -= pur["amount"]

        daily_records.append({"Date": curr_date, "Balance": current_balance})

    return pd.DataFrame(daily_records)


def run_monte_carlo_cashflow(starting_balance, forecast_days, income_rules, expense_rules, iterations=100, std_dev_pct=0.05):
    """Runs Monte Carlo simulations on cash balances using NumPy vectorization."""
    base_df = calculate_cashflow(starting_balance, forecast_days, income_rules, expense_rules, [])
    dates = base_df["Date"].values
    base_balances = base_df["Balance"].values

    # Generate random daily spending fluctuations around the base line
    daily_changes = np.diff(base_balances, prepend=starting_balance)
    noise = np.random.normal(0, np.abs(daily_changes) * std_dev_pct + 1.0, (iterations, forecast_days))
    
    simulated_paths = np.cumsum(daily_changes + noise, axis=1)
    
    p10 = np.percentile(simulated_paths, 10, axis=0)
    p50 = np.percentile(simulated_paths, 50, axis=0)
    p90 = np.percentile(simulated_paths, 90, axis=0)

    return pd.DataFrame({
        "Date": dates,
        "P10_Unfavorable": p10,
        "P50_Expected": p50,
        "P90_Favorable": p90
    })