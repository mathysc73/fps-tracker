import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as flask_app  # noqa: E402


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "fps-tracker"
    assert data["players_tracked"] == 3


def test_get_all_players(client):
    response = client.get("/api/players")
    assert response.status_code == 200
    data = response.get_json()
    assert "ShadowFPS" in data
    assert "ValoAce" in data
    assert "WarzonePro" in data


def test_get_single_player(client):
    response = client.get("/api/players/ShadowFPS")
    assert response.status_code == 200
    data = response.get_json()
    assert data["kd_ratio"] > 0
    assert data["game"] == "CS2"


def test_get_unknown_player_returns_404(client):
    response = client.get("/api/players/Inconnu")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_leaderboard(client):
    response = client.get("/api/leaderboard")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    for i in range(len(data) - 1):
        assert data[i]["kd_ratio"] >= data[i + 1]["kd_ratio"]


def test_add_session(client):
    payload = {"kills": 20, "deaths": 10, "win": True, "hours": 1.5}
    response = client.post(
        "/api/players/ValoAce/session",
        json=payload,
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "new_kd" in data
    assert "new_wins" in data


def test_add_session_unknown_player(client):
    payload = {"kills": 5, "deaths": 3, "win": False, "hours": 0.5}
    response = client.post(
        "/api/players/Fantome/session",
        json=payload,
        content_type="application/json"
    )
    assert response.status_code == 404


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    text = response.data.decode("utf-8")
    assert "fps_tracker_requests_total" in text
    assert "fps_tracker_player_kd_ratio" in text
