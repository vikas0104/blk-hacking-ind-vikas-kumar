from app.services.tax_service import calculate_nps_tax_benefit
from app.services.period_rule_service import (
    apply_k_grouping,
    apply_p_rules,
    apply_q_rules,
)
from app.utils.constants import (
    INDEX_RATE,
    MIN_INVESTMENT_YEARS,
    NPS_RATE,
    RETIREMENT_AGE,
)


def _investment_years(age):
    diff = RETIREMENT_AGE - age
    return diff if diff > MIN_INVESTMENT_YEARS else MIN_INVESTMENT_YEARS


def _compound_interest(principal, rate, years):
    return principal * ((1 + rate) ** years)


def _inflation_adjust(amount, inflation, years):
    return amount / ((1 + inflation) ** years)


def calculate_returns(
    transactions, q_periods, p_periods, k_periods,
    age, wage, inflation, rate, is_nps=False,
):
    adjusted = apply_q_rules(transactions, q_periods)
    adjusted = apply_p_rules(adjusted, p_periods)

    total_amount = round(sum(t["amount"] for t in adjusted), 2)
    total_ceiling = round(sum(t["ceiling"] for t in adjusted), 2)

    savings_by_k = apply_k_grouping(adjusted, k_periods)

    years = _investment_years(age)
    annual_income = wage * 12

    savings_by_dates = []
    for saving in savings_by_k:
        invested = saving["amount"]
        future_value = _compound_interest(invested, rate, years)
        real_value = _inflation_adjust(future_value, inflation, years)
        profit = round(real_value - invested, 2)

        tax_benefit = 0.0
        if is_nps:
            tax_benefit = calculate_nps_tax_benefit(invested, annual_income)

        savings_by_dates.append({
            "start": saving["start"],
            "end": saving["end"],
            "amount": round(invested, 2),
            "profits": profit,
            "taxBenefit": tax_benefit,
        })

    return {
        "transactionsTotalAmount": total_amount,
        "transactionsTotalCeiling": total_ceiling,
        "savingsByDates": savings_by_dates,
    }


def calculate_nps_returns(
    transactions, q_periods, p_periods, k_periods,
    age, wage, inflation,
):
    return calculate_returns(
        transactions, q_periods, p_periods, k_periods,
        age, wage, inflation, NPS_RATE, is_nps=True,
    )


def calculate_index_returns(
    transactions, q_periods, p_periods, k_periods,
    age, wage, inflation,
):
    return calculate_returns(
        transactions, q_periods, p_periods, k_periods,
        age, wage, inflation, INDEX_RATE, is_nps=False,
    )
