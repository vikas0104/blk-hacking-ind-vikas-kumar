from datetime import datetime

from app.utils.constants import DATETIME_FMT


def _parse_dt(s):
    return datetime.strptime(s, DATETIME_FMT)


def _in_range(dt, start, end):
    return start <= dt <= end


def apply_q_rules(transactions, q_periods):
    """
    If multiple q periods match: use the one that starts latest (start date is closest to
    transaction date). If they start on the same date, use the first one in the list.
    """
    if not q_periods:
        return transactions

    indexed_q = []
    for i, qp in enumerate(q_periods):
        indexed_q.append({
            "fixed": qp["fixed"],
            "start": _parse_dt(qp["start"]),
            "end": _parse_dt(qp["end"]),
            "idx": i,
        })
    # timespanp is epoch time
    # so we sort by descending start time and ascending idx
    indexed_q.sort(key=lambda x: (-x["start"].timestamp(), x["idx"]))

    result = []
    for txn in transactions:
        txn_dt = _parse_dt(txn["date"])
        matched = False
        for qp in indexed_q:
            if _in_range(txn_dt, qp["start"], qp["end"]):
                result.append({**txn, "remanent": round(qp["fixed"], 2)})
                matched = True
                break
        if not matched:
            result.append(txn.copy())
    return result


def apply_p_rules(transactions, p_periods):
    """
    When a transaction date falls within a p period (including start and end dates), add the p
    period's extra amount to the remanent.
    If multiple p periods match: add all their extra amounts together. p periods always add
    to the remanent; they never replace it.
    p is an addition to q rules which means if a transaction falls in q and then p, we apply
    both.
    """
    if not p_periods:
        # print("no p periods, returning transactions as is")
        return transactions

    parsed_p = []
    for pp in p_periods:
        parsed_p.append({
            "extra": pp["extra"],
            "start": _parse_dt(pp["start"]),
            "end": _parse_dt(pp["end"]),
        })

    result = []
    for txn in transactions:
        txn_dt = _parse_dt(txn["date"])
        total_extra = sum(
            pp["extra"] for pp in parsed_p if _in_range(txn_dt, pp["start"], pp["end"])
        )
        new_remanent = txn.get("remanent", 0) + total_extra
        result.append({**txn, "remanent": round(new_remanent, 2)})
    # print("p result", result)
    return result


def apply_k_grouping(transactions, k_periods):
    """
    For each k period: sum up the remanent of all transactions whose dates fall between the
    k period's start and end dates (including both).
    • A transaction can belong to multiple k periods. Each k period calculates its sum
    independently.
    • Date ranges include both start and end dates.
    • Any k range is within a calendar year and not spanning multiple years.

    """
    savings = []
    for kp in k_periods:
        k_start = _parse_dt(kp["start"])
        k_end = _parse_dt(kp["end"])
        total = sum(
            txn["remanent"]
            for txn in transactions
            if _in_range(_parse_dt(txn["date"]), k_start, k_end)
        )
        savings.append({
            "start": kp["start"],
            "end": kp["end"],
            "amount": round(total, 2),
        })
    # print("k result", savings)
    return savings


def filter_transactions(transactions, q_periods, p_periods, k_periods):
    """
    Full filter pipeline: q -> p -> k.

    Returns valid (within at least one k period) and invalid transactions.
    """
    adjusted = apply_q_rules(transactions, q_periods)
    adjusted = apply_p_rules(adjusted, p_periods)

    if not k_periods:
        return {"valid": adjusted, "invalid": []}

    valid = []
    invalid = []
    parsed_k = [(_parse_dt(kp["start"]), _parse_dt(kp["end"])) for kp in k_periods]

    for txn in adjusted:
        txn_dt = _parse_dt(txn["date"])
        in_any_k = any(_in_range(txn_dt, ks, ke) for ks, ke in parsed_k)
        if in_any_k:
            valid.append(txn)
        else:
            invalid.append({
                **txn,
                "message": "Transaction date outside all k periods",
            })
    # print("filter result", valid, invalid)
    return {"valid": valid, "invalid": invalid}
