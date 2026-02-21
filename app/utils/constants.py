"""
Each expense is represented as expense[i] = {date: t, amount: x};
with 0 ≤ 𝑛 < 106
, 0 ≤ i, j ≤ n, t ∈ {w: w is a string of characters indicating a date-time in a fixed
format}, 𝑡𝑖 ≠ 𝑡𝑗
, 𝑥 < 5 × 10^5
).
"""
NPS_RATE = 0.0711
INDEX_RATE = 0.1449
DEFAULT_INFLATION = 0.055
RETIREMENT_AGE = 60
MIN_INVESTMENT_YEARS = 5

MAX_NPS_DEDUCTION = 200_000
NPS_DEDUCTION_INCOME_PCT = 0.10

MAX_AMOUNT = 500_000
ROUNDING_CONST = 100

DATETIME_FMT = "%Y-%m-%d %H:%M:%S"

TAX_SLABS = [
    (700_000, 0.00),
    (1_000_000, 0.10),
    (1_200_000, 0.15),
    (1_500_000, 0.20),
    (float("inf"), 0.30),
]
