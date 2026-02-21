import os
import threading

import psutil
from flask import Blueprint, jsonify

from app import get_uptime

performance_bp = Blueprint(
    "performance", __name__, url_prefix="/blackrock/challenge/v1"
)


@performance_bp.route("/performance", methods=["GET"])
def performance():
    uptime_s = get_uptime()
    hours = int(uptime_s // 3600)
    minutes = int((uptime_s % 3600) // 60)
    seconds = uptime_s % 60
    time_str = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / (1024 * 1024)
    memory_str = f"{memory_mb:.2f} MB"

    thread_count = threading.active_count()

    return jsonify({
        "time": time_str,
        "memory": memory_str,
        "threads": thread_count,
    })
