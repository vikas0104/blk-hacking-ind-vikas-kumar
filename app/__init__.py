import time
from flask import Flask

_start_time = time.time()


def get_uptime() -> float:
    return time.time() - _start_time


def create_app() -> Flask:
    app = Flask(__name__)

    from app.routes.transactions import transactions_bp
    from app.routes.returns import returns_bp
    from app.routes.performance import performance_bp

    app.register_blueprint(transactions_bp)
    app.register_blueprint(returns_bp)
    app.register_blueprint(performance_bp)

    return app
