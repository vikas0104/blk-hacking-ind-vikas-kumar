
import json
import pytest

from app.services.tax_service import calculate_tax, calculate_nps_tax_benefit
from app.services.investment_service import (
    _investment_years,
    _compound_interest,
    _inflation_adjust,
    calculate_nps_returns,
    calculate_index_returns,
)


class TestTaxCalculation:
    def test_zero_slab(self):
        assert calculate_tax(600_000) == 0
        assert calculate_tax(700_000) == 0

    def test_ten_percent_slab(self):
        assert calculate_tax(800_000) == 10_000  # (800k - 700k) * 10%

    def test_fifteen_percent_slab(self):
        expected = 30_000 + 15_000  # 10% on 3L + 15% on 1L
        assert calculate_tax(1_100_000) == expected

    def test_twenty_percent_slab(self):
        expected = 30_000 + 30_000 + 20_000  # 10% on 3L + 15% on 2L + 20% on 1L
        assert calculate_tax(1_300_000) == expected

    def test_thirty_percent_slab(self):
        expected = 30_000 + 30_000 + 60_000 + 30_000  # 10%*3L + 15%*2L + 20%*3L + 30%*1L
        assert calculate_tax(1_600_000) == expected

    def test_boundary_700k(self):
        assert calculate_tax(700_001) == pytest.approx(0.1, abs=0.01)


class TestNPSTaxBenefit:
    def test_below_tax_threshold(self):
        benefit = calculate_nps_tax_benefit(145, 600_000)
        assert benefit == 0  # income 600k is in 0% slab

    def test_deduction_limited_by_invested(self):
        benefit = calculate_nps_tax_benefit(100, 1_000_000)
        expected = calculate_tax(1_000_000) - calculate_tax(1_000_000 - 100)
        assert benefit == expected

    def test_deduction_limited_by_income_pct(self):
        benefit = calculate_nps_tax_benefit(500_000, 1_000_000)
        nps_ded = min(500_000, 0.10 * 1_000_000, 200_000)  # 100_000
        expected = calculate_tax(1_000_000) - calculate_tax(1_000_000 - nps_ded)
        assert benefit == expected

    def test_deduction_limited_by_max(self):
        benefit = calculate_nps_tax_benefit(500_000, 5_000_000)
        nps_ded = min(500_000, 0.10 * 5_000_000, 200_000)  # 200_000
        expected = calculate_tax(5_000_000) - calculate_tax(5_000_000 - nps_ded)
        assert benefit == expected


class TestInvestmentYears:
    def test_normal_age(self):
        assert _investment_years(29) == 31
        assert _investment_years(30) == 30

    def test_near_retirement(self):
        assert _investment_years(55) == 5
        assert _investment_years(56) == 5  # min 5 years

    def test_at_retirement(self):
        assert _investment_years(60) == 5

    def test_over_retirement(self):
        assert _investment_years(65) == 5


class TestCompoundInterest:
    def test_basic(self):
        result = _compound_interest(1000, 0.10, 1)
        assert result == pytest.approx(1100, abs=0.01)

    def test_nps_rate(self):
        result = _compound_interest(145, 0.0711, 31)
        assert result == pytest.approx(1219, abs=5)  # ~1219.45 per example


class TestInflationAdjust:
    def test_basic(self):
        result = _inflation_adjust(1000, 0.05, 1)
        assert result == pytest.approx(952.38, abs=0.01)

    def test_nps_example(self):
        future_value = _compound_interest(145, 0.0711, 31)
        real_value = _inflation_adjust(future_value, 0.055, 31)
        assert real_value == pytest.approx(231.9, abs=2)


class TestChallengeExample:
    """Full end-to-end test using the example from the challenge document."""

    TRANSACTIONS = [
        {"date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
        {"date": "2023-02-28 15:49:00", "amount": 375, "ceiling": 400, "remanent": 25},
        {"date": "2023-07-01 21:59:00", "amount": 620, "ceiling": 700, "remanent": 80},
        {"date": "2023-12-17 08:09:00", "amount": 480, "ceiling": 500, "remanent": 20},
    ]
    Q = [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00"}]
    P = [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:00"}]
    K = [
        {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:00"},
        {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"},
    ]

    def test_nps_returns(self):
        result = calculate_nps_returns(
            self.TRANSACTIONS, self.Q, self.P, self.K,
            age=29, wage=50_000, inflation=0.055,
        )
        assert result["transactionsTotalAmount"] == 1725
        assert result["transactionsTotalCeiling"] == 1900
        assert len(result["savingsByDates"]) == 2

        k1 = result["savingsByDates"][0]
        assert k1["amount"] == 75
        assert k1["taxBenefit"] == 0  # 600k income is in 0% slab

        k2 = result["savingsByDates"][1]
        assert k2["amount"] == 145
        assert k2["profits"] == pytest.approx(86.88, abs=2)
        assert k2["taxBenefit"] == 0

    def test_index_returns(self):
        result = calculate_index_returns(
            self.TRANSACTIONS, self.Q, self.P, self.K,
            age=29, wage=50_000, inflation=0.055,
        )
        k2 = result["savingsByDates"][1]
        assert k2["amount"] == 145
        real_return = k2["amount"] + k2["profits"]
        assert real_return == pytest.approx(1829.5, abs=5)
        assert k2["taxBenefit"] == 0


class TestNPSEndpoint:
    def test_nps(self, client):
        payload = {
            "age": 29,
            "wage": 50000,
            "inflation": 0.055,
            "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00"}],
            "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:00"}],
            "k": [
                {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:00"},
                {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"},
            ],
            "transactions": [
                {"date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
                {"date": "2023-02-28 15:49:00", "amount": 375, "ceiling": 400, "remanent": 25},
                {"date": "2023-07-01 21:59:00", "amount": 620, "ceiling": 700, "remanent": 80},
                {"date": "2023-12-17 08:09:00", "amount": 480, "ceiling": 500, "remanent": 20},
            ],
        }
        resp = client.post(
            "/blackrock/challenge/v1/returns:nps",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["savingsByDates"][1]["amount"] == 145


class TestIndexEndpoint:
    def test_index(self, client):
        payload = {
            "age": 29,
            "wage": 50000,
            "inflation": 0.055,
            "q": [],
            "p": [],
            "k": [{"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"}],
            "transactions": [
                {"date": "2023-06-15 12:00:00", "amount": 250, "ceiling": 300, "remanent": 50},
            ],
        }
        resp = client.post(
            "/blackrock/challenge/v1/returns:index",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["savingsByDates"][0]["taxBenefit"] == 0
