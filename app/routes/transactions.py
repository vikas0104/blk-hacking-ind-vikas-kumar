from flask import Blueprint, jsonify, request

from app.services.transaction_service import parse_expenses, validate_transactions
from app.services.period_rule_service import filter_transactions

transactions_bp = Blueprint(
    "transactions", __name__, url_prefix="/blackrock/challenge/v1"
)


@transactions_bp.route("/transactions:parse", methods=["POST"])
def parse():
    data = request.get_json(force=True)
    expenses = data.get("expenses", [])
    transactions = parse_expenses(expenses)
    return jsonify({"transactions": transactions})


@transactions_bp.route("/transactions:validator", methods=["POST"])
def validator():
    data = request.get_json(force=True)
    wage = data.get("wage", 0)
    transactions = data.get("transactions", [])
    result = validate_transactions(wage, transactions)
    return jsonify(result)


@transactions_bp.route("/transactions:filter", methods=["POST"])
def filter_route():
    data = request.get_json(force=True)
    q_periods = data.get("q", [])
    p_periods = data.get("p", [])
    k_periods = data.get("k", [])
    transactions = data.get("transactions", [])
    result = filter_transactions(transactions, q_periods, p_periods, k_periods)
    return jsonify(result)
