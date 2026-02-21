from flask import Blueprint, jsonify, request

from app.services.investment_service import (
    calculate_index_returns,
    calculate_nps_returns,
)

returns_bp = Blueprint("returns", __name__, url_prefix="/blackrock/challenge/v1")


def _extract_common_params(data: dict) -> dict:
    return {
        "transactions": data.get("transactions", []),
        "q_periods": data.get("q", []),
        "p_periods": data.get("p", []),
        "k_periods": data.get("k", []),
        "age": data.get("age", 30),
        "wage": data.get("wage", 0),
        "inflation": data.get("inflation", 0.055),
    }


@returns_bp.route("/returns:nps", methods=["POST"])
def nps():
    data = request.get_json(force=True)
    params = _extract_common_params(data)
    result = calculate_nps_returns(**params)
    return jsonify(result)


@returns_bp.route("/returns:index", methods=["POST"])
def index():
    data = request.get_json(force=True)
    params = _extract_common_params(data)
    result = calculate_index_returns(**params)
    return jsonify(result)
