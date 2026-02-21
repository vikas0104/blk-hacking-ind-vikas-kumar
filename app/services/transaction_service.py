import math
from datetime import datetime

from app.utils.constants import DATETIME_FMT, MAX_AMOUNT, ROUNDING_CONST


def compute_ceiling(amount):
    return math.ceil(amount / ROUNDING_CONST) * ROUNDING_CONST


def parse_expenses(expenses):
    transactions = []
    for exp in expenses:
        amount = exp["amount"]
        ceiling = compute_ceiling(amount)
        remanent = ceiling - amount
        transactions.append({
            "date": exp["timestamp"],
            "amount": round(amount, 2),
            "ceiling": round(ceiling, 2),
            "remanent": round(remanent, 2),
        })
    return transactions


def _parse_date(date_str):
    try:
        return datetime.strptime(date_str, DATETIME_FMT)
    except (ValueError, TypeError):
        return None


def validate_transactions(wage, transactions):
    valid = []
    invalid = []
    seen_dates = {}

    for idx, txn in enumerate(transactions):
        errors = []

        date_str = txn.get("date", "")
        dt = _parse_date(date_str)
        if dt is None:
            errors.append(f"Invalid date format: {date_str}")

        amount = txn.get("amount")
        if amount is None or not isinstance(amount, (int, float)):
            errors.append("Amount must be a number")
        elif amount < 0 or amount >= MAX_AMOUNT:
            errors.append(f"Amount {amount} out of range [0, {MAX_AMOUNT})")

        if not errors and isinstance(amount, (int, float)):
            expected_ceiling = compute_ceiling(amount)
            expected_remanent = expected_ceiling - amount

            ceiling = txn.get("ceiling")
            remanent = txn.get("remanent")

            if ceiling is None or round(ceiling, 2) != round(expected_ceiling, 2):
                errors.append(
                    f"Ceiling mismatch: expected {expected_ceiling}, got {ceiling}"
                )
            if remanent is None or round(remanent, 2) != round(expected_remanent, 2):
                errors.append(
                    f"Remanent mismatch: expected {expected_remanent}, got {remanent}"
                )

        if date_str in seen_dates:
            errors.append(f"Duplicate date: {date_str}")
        else:
            seen_dates[date_str] = idx

        if errors:
            invalid.append({**txn, "message": "; ".join(errors)})
        else:
            valid.append(txn)

    return {"valid": valid, "invalid": invalid}
