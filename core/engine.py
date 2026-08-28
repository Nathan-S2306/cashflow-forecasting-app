from datetime import date, timedelta
import numpy as np
import pandas as pd


def adjust_weekend_preceding_friday(dt: date) -> date:
    """Shifts Saturday or Sunday dates back to the preceding Friday."""
    if dt.weekday() == 5:  # Saturday
        return dt - timedelta(days=1)
    elif dt.weekday() == 6:  # Sunday
        return dt - timedelta(days=2)
    return dt


def is_last_working_day(dt: date) -> bool:
    """Checks if a given date is the last working day of its calendar month."""
    # Find the last calendar day of the current month
    if dt.month == 12:
        next_month_first = date(dt.year + 1, 1, 1)
    else:
        next_month_first = date(dt.year, dt.month + 1, 1)
    
    last_cal_day = next_month_first - timedelta(days=1)
    target_working_day = adjust_weekend_preceding_friday(last_cal_day)
    return dt == target_working_day


def is_last_friday(dt: date) -> bool:
    """Checks if a given date is the last Friday of its calendar month."""
    return dt.weekday() == 4 and (dt + timedelta(days=7)).month != dt.month


def is_rule_due(rule: dict, curr_date: date) -> bool:
    """Evaluates whether an income or expense rule triggers on curr_date."""
    freq = rule.get("freq", "Monthly")

    # Parse anchor_date if provided as string (ISO format: 'YYYY-MM-DD')
    anchor = rule.get("anchor_date")
    if isinstance(anchor, str):
        anchor = date.fromisoformat(anchor)

    if freq == "Monthly":
        target_day = rule.get("day", 1)
        
        # Clamp target day to maximum days in current month (e.g., 31st in Feb becomes 28th/29th)
        if curr_date.month == 12:
            next_month_first = date(curr_date.year + 1, 1, 1)
        else:
            next_month_first = date(curr_date.year, curr_date.month + 1, 1)
        last_month_day = (next_month_first - timedelta(days=1)).day
        actual_day = min(target_day, last_month_day)

        raw_target_date = date(curr_date.year, curr_date.month, actual_day)

        # Shift to preceding Friday if configured and lands on a weekend
        if rule.get("shift_weekend", False):
            final_target_date = adjust_weekend_preceding_friday(raw_target_date)
        else:
            final_target_date = raw_target_date

        return curr_date == final_target_date

    elif freq == "4-Weekly":
        if not anchor:
            return False
        delta_days = (curr_date - anchor).days
        return delta_days >= 0 and delta_days % 28 == 0

    elif freq == "Bi-Weekly":
        if not anchor:
            return False
        delta_days = (curr_date - anchor).days
        return delta_days >= 0 and delta_days % 14 == 0

    elif freq == "Weekly":
        if anchor:
            delta_days = (curr_date - anchor).days
            return delta_days >= 0 and delta_days % 7 == 0
        # Fallback: defaults to Mondays (0) or specified day_of_week
        target_weekday = rule.get("day_of_week", 0)
        return curr_date.weekday() == target_weekday

    elif freq == "Last Working Day":
        return is_last_working_day(curr_date)

    elif freq == "Last Friday":
        return is_last_friday(curr_date)

    return False


def calculate_cashflow(starting_balance, forecast_days, income_rules, expense_rules, planned_purchases):
    """Calculates day-by-day cash balance projections supporting advanced pay cycles."""
    start_date = date.today()
    date_range = [start_date + timedelta(days=i) for i in range(forecast_days)]

    daily_records = []
    current_balance = float(starting_balance)

    for curr_date in date_range:
        day_str = curr_date.strftime("%Y-%m-%d")

        # Inflows
        for inc in income_rules:
            if is_rule_due(inc, curr_date):
                current_balance += inc["amount"]

        # Outflows
        for exp in expense_rules:
            if is_rule_due(exp, curr_date):
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