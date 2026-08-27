import hashlib
from datetime import datetime
import pandas as pd
from core.db import save_bulk_transactions

CATEGORY_KEYWORDS = {
    "Housing": ["mortgage", "rent", "council tax", "service charge"],
    "Bills": ["electric", "gas", "water", "broadband", "ee", "vodafone", "utility", "insurance"],
    "Subscriptions": ["netflix", "spotify", "amazon prime", "gym", "apple", "disney"],
    "Groceries & Living": ["tesco", "sainsbury", "asda", "morrisons", "aldi", "lidl", "waitrose", "boots"],
    "Transport": ["uber", "trainline", "shell", "bp", "bus", "petrol"],
    "Fun": ["pub", "restaurant", "nandos", "steam", "cinema"],
}


def guess_category(description: str) -> str:
    desc_lower = str(description).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return "General"


def parse_bank_statement(file_buffer) -> dict:
    df = pd.read_csv(file_buffer)
    df.columns = [str(c).strip().lower() for c in df.columns]

    date_col = next((c for c in df.columns if any(k in c for k in ["date", "time"])), None)
    desc_col = next((c for c in df.columns if any(k in c for k in ["desc", "payee", "title", "name", "narrative"])), None)
    amount_col = next((c for c in df.columns if "amount" in c and "debit" not in c and "credit" not in c), None)
    debit_col = next((c for c in df.columns if "debit" in c or "paid out" in c or "out" in c), None)
    credit_col = next((c for c in df.columns if "credit" in c or "paid in" in c or "in" in c), None)

    if not date_col or not desc_col:
        raise ValueError("Could not locate required Date and Description columns in CSV.")

    parsed_incomes, parsed_expenses, tx_hashes = [], [], []

    for _, row in df.iterrows():
        desc = str(row[desc_col]).strip()

        amount = 0.0
        if amount_col and pd.notna(row[amount_col]):
            amount = float(row[amount_col])
        elif debit_col or credit_col:
            deb = float(row[debit_col]) if debit_col and pd.notna(row[debit_col]) else 0.0
            cred = float(row[credit_col]) if credit_col and pd.notna(row[credit_col]) else 0.0
            amount = cred - deb

        if amount == 0.0:
            continue

        raw_date = str(row[date_col])
        try:
            parsed_dt = pd.to_datetime(raw_date, dayfirst=True, format="mixed", errors="coerce")
            if pd.isna(parsed_dt):
                parsed_dt = datetime.today()
        except Exception:
            parsed_dt = datetime.today()

        day_of_month = int(parsed_dt.day)
        formatted_date = parsed_dt.strftime("%Y-%m-%d")

        # MD5 Deduplication Hash
        hash_str = f"{formatted_date}_{desc}_{amount}"
        tx_hash = hashlib.md5(hash_str.encode("utf-8")).hexdigest()
        tx_hashes.append(tx_hash)

        category = guess_category(desc)

        if amount > 0:
            parsed_incomes.append({
                "name": desc,
                "amount": abs(amount),
                "day": day_of_month,
                "freq": "Monthly"
            })
        else:
            parsed_expenses.append({
                "name": desc,
                "amount": abs(amount),
                "day": day_of_month,
                "freq": "Monthly",
                "category": category,
                "date": formatted_date
            })

    return {
        "incomes": parsed_incomes,
        "expenses": parsed_expenses,
        "hashes": tx_hashes
    }


def process_bank_import(file_buffer, import_type: str = "recurring"):
    data = parse_bank_statement(file_buffer)
    return save_bulk_transactions(data["incomes"], data["expenses"], data["hashes"], import_type=import_type)