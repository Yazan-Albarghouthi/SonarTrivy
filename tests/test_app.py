from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_note():
    payload = {
        "title": "First note",
        "content": "This is a test note",
        "owner": "malik",
        "is_private": False,
    }

    response = client.post("/notes", json=payload)

    assert response.status_code == 200
    assert response.json()["title"] == "First note"


def test_list_notes():
    response = client.get("/notes")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_calculator_with_normal_expression():
    response = client.post("/calculate", json={"expression": "1 + 2"})

    assert response.status_code == 200
    assert response.json()["result"] == 3


def test_ratio_with_valid_input():
    response = client.get("/ratio?total=10&count=2")

    assert response.status_code == 200
    assert response.json()["ratio"] == 5