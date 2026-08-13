import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def run_cashflow_engine(
    current_balance: float,
    transactions_df: pd.DataFrame,
    projection_days: int = 90,
    min_safety_buffer: float = 100.0
) -> dict:
    transactions_df['date'] = pd.to_datetime(transactions_df['date'])
    transactions_df = transactions_df.sort_values('date')
    
    # 1. Fixed vs Variable Split
    fixed_mask = transactions_df['is_recurring'] == True
    fixed_txs = transactions_df[fixed_mask]
    variable_txs = transactions_df[~fixed_mask & (transactions_df['amount'] < 0)]
    
    # Calculate daily variable burn rate
    total_variable_spend = variable_txs['amount'].sum()
    historical_days_count = (transactions_df['date'].max() - transactions_df['date'].min()).days or 30
    daily_variable_burn = abs(total_variable_spend) / historical_days_count
    
    # 2. Timeline Grid
    today = datetime.now().date()
    future_dates = [today + timedelta(days=i) for i in range(projection_days)]
    
    projection_df = pd.DataFrame({'date': future_dates})
    projection_df['date'] = pd.to_datetime(projection_df['date'])
    projection_df['fixed_inflow'] = 0.0
    projection_df['fixed_outflow'] = 0.0
    projection_df['variable_estimate'] = -daily_variable_burn
    
    # 3. Map Recurring Items
    for _, item in fixed_txs.iterrows():
        day_of_month = item['day_of_month']
        amount = item['amount']
        mask = projection_df['date'].dt.day == day_of_month
        if amount > 0:
            projection_df.loc[mask, 'fixed_inflow'] += amount
        else:
            projection_df.loc[mask, 'fixed_outflow'] += abs(amount)
            
    # 4. Compute Cumulative Balance
    projection_df['net_daily_change'] = (
        projection_df['fixed_inflow'] 
        - projection_df['fixed_outflow'] 
        + projection_df['variable_estimate']
    )
    projection_df['projected_balance'] = current_balance + projection_df['net_daily_change'].cumsum()
    
    # 5. True Safe Cushion Calculation
    next_income_row = projection_df[projection_df['fixed_inflow'] > 0].head(1)
    if not next_income_row.empty:
        next_income_date = next_income_row['date'].values[0]
        bills_before_income = projection_df[projection_df['date'] < next_income_date]['fixed_outflow'].sum()
    else:
        bills_before_income = projection_df['fixed_outflow'].head(30).sum()
        
    true_safe_cushion = current_balance - bills_before_income - min_safety_buffer
    
    # Overdraft Warnings
    at_risk_days = projection_df[projection_df['projected_balance'] < min_safety_buffer]
    alerts = []
    if not at_risk_days.empty:
        first_risk = at_risk_days.iloc[0]
        days_until_risk = (first_risk['date'].date() - today).days
        alerts.append({
            "type": "OVERDRAFT_WARNING",
            "date": first_risk['date'].strftime('%Y-%m-%d'),
            "days_away": days_until_risk,
            "projected_balance": round(first_risk['projected_balance'], 2)
        })
        
    return {
        "current_balance": current_balance,
        "true_safe_cushion": round(true_safe_cushion, 2),
        "daily_burn_rate": round(daily_variable_burn, 2),
        "alerts": alerts,
        "projection_data": projection_df
    }

if __name__ == "__main__":
    mock_history = pd.DataFrame([
        {"date": "2026-07-28", "description": "Employer Payroll", "amount": 2800.00, "is_recurring": True, "day_of_month": 28},
        {"date": "2026-08-01", "description": "Landlord Rent", "amount": -1100.00, "is_recurring": True, "day_of_month": 1},
        {"date": "2026-08-05", "description": "Energy Bill", "amount": -120.00, "is_recurring": True, "day_of_month": 5},
        {"date": "2026-08-02", "description": "Groceries", "amount": -65.40, "is_recurring": False, "day_of_month": None},
        {"date": "2026-08-07", "description": "Coffee Shop", "amount": -14.20, "is_recurring": False, "day_of_month": None},
    ])
    
    result = run_cashflow_engine(current_balance=850.00, transactions_df=mock_history)
    
    print(f"--- ANACONDA ENGINE TEST RUN ---")
    print(f"Current Balance:   £{result['current_balance']}")
    print(f"True Safe Cushion: £{result['true_safe_cushion']}")
    print(f"Daily Burn Rate:   £{result['daily_burn_rate']}/day")
    print(f"\nForward Projections Preview:")
    print(result['projection_data'][['date', 'fixed_inflow', 'fixed_outflow', 'projected_balance']].head(7))