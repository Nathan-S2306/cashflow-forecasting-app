import os
import pytest
from core.db import add_debt, add_expense_rule, add_income_rule, init_db, load_debts
from views.tab_overview import calculate_cashflow_timeline


@pytest.fixture(autouse=True)
def setup_test_database():
    if os.path.exists("cashflow.db"):
        os.remove("cashflow.db")
    init_db()


def test_cashflow_timeline_calculation():
    add_income_rule("Salary", 2000.0, 1)
    add_expense_rule("Rent", 800.0, 5, category="Housing")

    df = calculate_cashflow_timeline(start_balance=1000.0, days=30)

    assert not df.empty
    assert "Balance" in df.columns
    assert df["Balance"].iloc[-1] == 2200.0


def test_stepchange_debt_priority_sorting():
    add_debt("Credit Card", 1000.0, 19.9, 30.0, is_priority=0)
    add_debt("Council Tax Arrears", 500.0, 0.0, 50.0, is_priority=1)

    debts = load_debts()
    assert len(debts) == 2

    council_tax = next(d for d in debts if d[1] == "Council Tax Arrears")
    credit_card = next(d for d in debts if d[1] == "Credit Card")

    assert council_tax[5] == 1
    assert credit_card[5] == 0