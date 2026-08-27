import json
import sqlite3
from typing import List, Tuple
import streamlit as st

DB_NAME = "cashflow.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        # Income rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                day INTEGER NOT NULL,
                freq TEXT NOT NULL DEFAULT 'Monthly'
            )
        """)

        # Expense rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expense_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                day INTEGER NOT NULL,
                freq TEXT NOT NULL DEFAULT 'Monthly',
                category TEXT DEFAULT 'General'
            )
        """)

        # Planned one-off purchases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS planned_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                category TEXT DEFAULT 'General'
            )
        """)

        # Debts table with StepChange priority flag
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                balance REAL NOT NULL,
                interest_rate REAL NOT NULL,
                min_payment REAL NOT NULL,
                is_priority INTEGER DEFAULT 0
            )
        """)

        # Savings goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL NOT NULL DEFAULT 0.0,
                target_date TEXT NOT NULL,
                monthly_contrib REAL DEFAULT 0.0
            )
        """)

        # Feedback backlog table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Statement transaction hashes for deduplication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS imported_hashes (
                tx_hash TEXT PRIMARY KEY,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

        # Schema Migration Safeguards
        cursor.execute("PRAGMA table_info(expense_rules)")
        exp_cols = [col[1] for col in cursor.fetchall()]
        if "category" not in exp_cols:
            cursor.execute("ALTER TABLE expense_rules ADD COLUMN category TEXT DEFAULT 'General'")

        cursor.execute("PRAGMA table_info(planned_purchases)")
        pur_cols = [col[1] for col in cursor.fetchall()]
        if "category" not in pur_cols:
            cursor.execute("ALTER TABLE planned_purchases ADD COLUMN category TEXT DEFAULT 'General'")

        cursor.execute("PRAGMA table_info(debts)")
        debt_cols = [col[1] for col in cursor.fetchall()]
        if "is_priority" not in debt_cols:
            cursor.execute("ALTER TABLE debts ADD COLUMN is_priority INTEGER DEFAULT 0")

        conn.commit()


def clear_db_cache():
    st.cache_data.clear()


# --- CACHED READ OPERATIONS ---
@st.cache_data(ttl=300)
def load_income_rules() -> List[Tuple]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, amount, day, freq FROM income_rules")
        return cursor.fetchall()


@st.cache_data(ttl=300)
def load_expense_rules() -> List[Tuple]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, amount, day, freq, category FROM expense_rules")
        return cursor.fetchall()


@st.cache_data(ttl=300)
def load_planned_purchases() -> List[Tuple]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, amount, date, category FROM planned_purchases")
        return cursor.fetchall()


@st.cache_data(ttl=300)
def load_debts() -> List[Tuple]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, balance, interest_rate, min_payment, is_priority FROM debts")
        return cursor.fetchall()


@st.cache_data(ttl=300)
def load_savings_goals() -> List[Tuple]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, target_amount, current_amount, target_date, monthly_contrib FROM savings_goals")
        return cursor.fetchall()


@st.cache_data(ttl=300)
def load_feedback() -> List[Tuple]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, text, created_at FROM feedback ORDER BY created_at DESC")
        return cursor.fetchall()


# --- SINGLE WRITE OPERATIONS ---
def add_income_rule(name: str, amount: float, day: int, freq: str = "Monthly"):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO income_rules (name, amount, day, freq) VALUES (?, ?, ?, ?)", (name, amount, day, freq))
        conn.commit()
    clear_db_cache()


def delete_income_rule(rule_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM income_rules WHERE id = ?", (rule_id,))
        conn.commit()
    clear_db_cache()


def add_expense_rule(name: str, amount: float, day: int, freq: str = "Monthly", category: str = "General"):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expense_rules (name, amount, day, freq, category) VALUES (?, ?, ?, ?, ?)", (name, amount, day, freq, category))
        conn.commit()
    clear_db_cache()


def delete_expense_rule(rule_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expense_rules WHERE id = ?", (rule_id,))
        conn.commit()
    clear_db_cache()


def add_planned_purchase(name: str, amount: float, date_str: str, category: str = "General"):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO planned_purchases (name, amount, date, category) VALUES (?, ?, ?, ?)", (name, amount, date_str, category))
        conn.commit()
    clear_db_cache()


def delete_planned_purchase(purchase_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM planned_purchases WHERE id = ?", (purchase_id,))
        conn.commit()
    clear_db_cache()


def add_debt(name: str, balance: float, interest_rate: float, min_payment: float, is_priority: int = 0):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO debts (name, balance, interest_rate, min_payment, is_priority) VALUES (?, ?, ?, ?, ?)", (name, balance, interest_rate, min_payment, is_priority))
        conn.commit()
    clear_db_cache()


def delete_debt(debt_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM debts WHERE id = ?", (debt_id,))
        conn.commit()
    clear_db_cache()


def add_savings_goal(name: str, target_amount: float, current_amount: float, target_date: str, monthly_contrib: float):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO savings_goals (name, target_amount, current_amount, target_date, monthly_contrib) VALUES (?, ?, ?, ?, ?)", (name, target_amount, current_amount, target_date, monthly_contrib))
        conn.commit()
    clear_db_cache()


def delete_savings_goal(goal_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
        conn.commit()
    clear_db_cache()


def add_feedback(category: str, text: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO feedback (category, text) VALUES (?, ?)", (category, text))
        conn.commit()
    clear_db_cache()


# --- BULK BATCH OPERATIONS ---
def save_bulk_transactions(incomes: list, expenses: list, hashes: list, import_type: str = "recurring") -> Tuple[int, int]:
    inserted_inc, inserted_exp = 0, 0
    with get_connection() as conn:
        cursor = conn.cursor()

        # Insert novel hashes
        valid_hashes = []
        for h in hashes:
            cursor.execute("SELECT tx_hash FROM imported_hashes WHERE tx_hash = ?", (h,))
            if not cursor.fetchone():
                valid_hashes.append((h,))

        if not valid_hashes:
            return 0, 0

        cursor.executemany("INSERT INTO imported_hashes (tx_hash) VALUES (?)", valid_hashes)

        if incomes:
            inc_data = [(i["name"], i["amount"], i["day"], i["freq"]) for i in incomes]
            cursor.executemany("INSERT INTO income_rules (name, amount, day, freq) VALUES (?, ?, ?, ?)", inc_data)
            inserted_inc = len(inc_data)

        if expenses:
            if import_type == "recurring":
                exp_data = [(e["name"], e["amount"], e["day"], e["freq"], e["category"]) for e in expenses]
                cursor.executemany("INSERT INTO expense_rules (name, amount, day, freq, category) VALUES (?, ?, ?, ?, ?)", exp_data)
            else:
                pur_data = [(e["name"], e["amount"], e["date"], e["category"]) for e in expenses]
                cursor.executemany("INSERT INTO planned_purchases (name, amount, date, category) VALUES (?, ?, ?, ?)", pur_data)
            inserted_exp = len(expenses)

        conn.commit()

    clear_db_cache()
    return inserted_inc, inserted_exp


# --- BACKUP EXPORT / IMPORT ---
def export_system_data() -> str:
    data = {
        "income_rules": load_income_rules(),
        "expense_rules": load_expense_rules(),
        "planned_purchases": load_planned_purchases(),
        "debts": load_debts(),
        "savings_goals": load_savings_goals(),
    }
    return json.dumps(data, indent=2)


def import_system_data(json_str: str):
    data = json.loads(json_str)
    with get_connection() as conn:
        cursor = conn.cursor()

        if "income_rules" in data:
            cursor.execute("DELETE FROM income_rules")
            for item in data["income_rules"]:
                cursor.execute("INSERT INTO income_rules (name, amount, day, freq) VALUES (?, ?, ?, ?)", (item[1], item[2], item[3], item[4]))

        if "expense_rules" in data:
            cursor.execute("DELETE FROM expense_rules")
            for item in data["expense_rules"]:
                cat = item[5] if len(item) > 5 else "General"
                cursor.execute("INSERT INTO expense_rules (name, amount, day, freq, category) VALUES (?, ?, ?, ?, ?)", (item[1], item[2], item[3], item[4], cat))

        if "planned_purchases" in data:
            cursor.execute("DELETE FROM planned_purchases")
            for item in data["planned_purchases"]:
                cat = item[4] if len(item) > 4 else "General"
                cursor.execute("INSERT INTO planned_purchases (name, amount, date, category) VALUES (?, ?, ?, ?)", (item[1], item[2], item[3], cat))

        if "debts" in data:
            cursor.execute("DELETE FROM debts")
            for item in data["debts"]:
                prio = item[5] if len(item) > 5 else 0
                cursor.execute("INSERT INTO debts (name, balance, interest_rate, min_payment, is_priority) VALUES (?, ?, ?, ?, ?)", (item[1], item[2], item[3], item[4], prio))

        if "savings_goals" in data:
            cursor.execute("DELETE FROM savings_goals")
            for item in data["savings_goals"]:
                cursor.execute("INSERT INTO savings_goals (name, target_amount, current_amount, target_date, monthly_contrib) VALUES (?, ?, ?, ?, ?)", (item[1], item[2], item[3], item[4], item[5]))

        conn.commit()
    clear_db_cache()