
class TestPerformanceEndpoint:
    def test_performance_response(self, client):
        resp = client.get("/blackrock/challenge/v1/performance")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "time" in data
        assert "memory" in data
        assert "threads" in data

    def test_time_format(self, client):
        resp = client.get("/blackrock/challenge/v1/performance")
        data = resp.get_json()
        parts = data["time"].split(":")
        assert len(parts) == 3

    def test_memory_format(self, client):
        resp = client.get("/blackrock/challenge/v1/performance")
        data = resp.get_json()
        assert data["memory"].endswith("MB")

    def test_threads_positive(self, client):
        resp = client.get("/blackrock/challenge/v1/performance")
        data = resp.get_json()
        assert isinstance(data["threads"], int)
        assert data["threads"] > 0
