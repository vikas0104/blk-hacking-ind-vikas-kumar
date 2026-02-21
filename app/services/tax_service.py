from app.utils.constants import (
    MAX_NPS_DEDUCTION,
    NPS_DEDUCTION_INCOME_PCT,
    TAX_SLABS,
)


def calculate_tax(income: float) -> float:
    """
    Calculate tax
    Slabs:
      0 - 7L:    0%
      7L - 10L:  10%
      10L - 12L: 15%
      12L - 15L: 20%
      15L+:      30%
    """
    if income <= TAX_SLABS[0][0]:
        return 0.0

    tax = 0.0
    prev_limit = 0.0
    for limit, rate in TAX_SLABS:
        if income <= limit:
            tax += (income - prev_limit) * rate
            break
        else:
            tax += (limit - prev_limit) * rate
        prev_limit = limit
    return round(tax, 2)


def calculate_nps_tax_benefit(
    invested, annual_income):
    """
    NPS tax benefit = Tax(income) - Tax(income - NPS_Deduction).
    NPS_Deduction = min(invested, 10% of annual_income, 2,00,000)
    """
    nps_deduction = min(
        invested,
        NPS_DEDUCTION_INCOME_PCT * annual_income,
        MAX_NPS_DEDUCTION,
    )
    benefit = calculate_tax(annual_income) - calculate_tax(
        annual_income - nps_deduction
    )
    return round(benefit, 2)
