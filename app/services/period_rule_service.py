from bisect import bisect_left, bisect_right
from datetime import datetime

from sortedcontainers import SortedList

from app.utils.constants import DATETIME_FMT


def _parse_dt(s):
    return datetime.strptime(s, DATETIME_FMT)


def apply_q_rules(transactions, q_periods):
    """Sweep-line approach: O((n + q) log(n + q)) instead of O(n * q).

    If multiple q periods match, use the one with the latest start.
    Ties broken by earliest position in the original list.
    """
    if not q_periods:
        return transactions

    parsed_q = []
    for i, qp in enumerate(q_periods):
        parsed_q.append((
            _parse_dt(qp["start"]),
            _parse_dt(qp["end"]),
            qp["fixed"],
            i,
        ))

    START, TXN, END = 0, 1, 2
    events = []
    for start, end, fixed, idx in parsed_q:
        events.append((start, START, idx, fixed, end))
        events.append((end, END, idx, fixed, end))

    txn_indices = {}
    for ti, txn in enumerate(transactions):
        dt = _parse_dt(txn["date"])
        events.append((dt, TXN, ti, None, None))
        txn_indices[ti] = dt

    events.sort(key=lambda e: (e[0], e[1]))

    # SortedList keyed by (-start_timestamp, idx) so first element = latest start, first in list
    active = SortedList(key=lambda x: (-x[0].timestamp(), x[1]))
    q_lookup = {}

    result = [None] * len(transactions)

    for ev in events:
        ev_time, ev_type, ev_id, ev_fixed, ev_end = ev

        if ev_type == START:
            entry = (parsed_q[ev_id][0], ev_id, ev_fixed)
            active.add(entry)
            q_lookup[ev_id] = entry

        elif ev_type == END:
            entry = q_lookup.pop(ev_id, None)
            if entry is not None:
                active.discard(entry)

        else:
            txn = transactions[ev_id]
            if active:
                best = active[0]
                result[ev_id] = {**txn, "remanent": round(best[2], 2)}
            else:
                result[ev_id] = txn.copy()

    return result


def apply_p_rules(transactions, p_periods):
    """Sweep-line with running sum: O((n + p) log(n + p)) instead of O(n * p).

    All matching p periods stack -- their extras are summed.
    """
    if not p_periods:
        return transactions

    ADD, TXN, REMOVE = 0, 1, 2
    events = []
    for pp in p_periods:
        start = _parse_dt(pp["start"])
        end = _parse_dt(pp["end"])
        extra = pp["extra"]
        events.append((start, ADD, extra, None))
        events.append((end, REMOVE, extra, None))

    for ti, txn in enumerate(transactions):
        dt = _parse_dt(txn["date"])
        events.append((dt, TXN, 0, ti))

    events.sort(key=lambda e: (e[0], e[1]))

    running_extra = 0.0
    result = [None] * len(transactions)

    for ev_time, ev_type, ev_val, ev_idx in events:
        if ev_type == ADD:
            running_extra += ev_val
        elif ev_type == REMOVE:
            running_extra -= ev_val
        else:
            txn = transactions[ev_idx]
            new_remanent = txn.get("remanent", 0) + running_extra
            result[ev_idx] = {**txn, "remanent": round(new_remanent, 2)}

    return result


def apply_k_grouping(transactions, k_periods):
    """Prefix-sum with binary search: O(n log n + k log n) instead of O(n * k).

    Each k period independently sums remanents of transactions within its range.
    A transaction can belong to multiple k periods.
    """
    if not transactions:
        return [
            {"start": kp["start"], "end": kp["end"], "amount": 0.0}
            for kp in k_periods
        ]

    paired = []
    for txn in transactions:
        paired.append((_parse_dt(txn["date"]), txn["remanent"]))
    paired.sort(key=lambda x: x[0])

    sorted_dates = [p[0] for p in paired]
    prefix = [0.0] * (len(paired) + 1)
    for i, (_, rem) in enumerate(paired):
        prefix[i + 1] = prefix[i] + rem

    savings = []
    for kp in k_periods:
        k_start = _parse_dt(kp["start"])
        k_end = _parse_dt(kp["end"])
        left = bisect_left(sorted_dates, k_start)
        right = bisect_right(sorted_dates, k_end)
        total = prefix[right] - prefix[left]
        savings.append({
            "start": kp["start"],
            "end": kp["end"],
            "amount": round(total, 2),
        })
    return savings


def filter_transactions(transactions, q_periods, p_periods, k_periods):
    """Full filter pipeline: q -> p -> k.

    Returns valid (within at least one k period) and invalid transactions.
    """
    adjusted = apply_q_rules(transactions, q_periods)
    adjusted = apply_p_rules(adjusted, p_periods)

    if not k_periods:
        return {"valid": adjusted, "invalid": []}

    parsed_k = [(_parse_dt(kp["start"]), _parse_dt(kp["end"])) for kp in k_periods]

    # Sort k ranges by start for efficient checking
    sorted_k = sorted(parsed_k)

    valid = []
    invalid = []

    for txn in adjusted:
        txn_dt = _parse_dt(txn["date"])
        in_any_k = any(ks <= txn_dt <= ke for ks, ke in sorted_k)
        if in_any_k:
            valid.append(txn)
        else:
            invalid.append({
                **txn,
                "message": "Transaction date outside all k periods",
            })

    return {"valid": valid, "invalid": invalid}
