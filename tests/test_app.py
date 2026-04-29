import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "sonarTrivy"}


def test_create_note():
    payload = {"title": "Test note", "content": "Some content here", "owner": "tester"}
    response = client.post("/notes", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test note"
    assert data["owner"] == "tester"


def test_create_note_invalid_title():
    payload = {"title": "ab", "content": "Some content here", "owner": "tester"}
    response = client.post("/notes", json=payload)
    assert response.status_code == 400


def test_create_note_invalid_content():
    payload = {"title": "Valid title", "content": "ab", "owner": "tester"}
    response = client.post("/notes", json=payload)
    assert response.status_code == 400


def test_list_notes():
    response = client.get("/notes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_note_by_id():
    payload = {"title": "Fetch me later", "content": "Content for fetching", "owner": "fetcher"}
    created = client.post("/notes", json=payload)
    note_id = created.json()["id"]

    response = client.get(f"/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["id"] == note_id


def test_get_note_not_found():
    response = client.get("/notes/999999")
    assert response.status_code == 404


def test_search_notes():
    payload = {
        "title": "Searchable note",
        "content": "uniquekeyword9876 content body",
        "owner": "searcher",
    }
    client.post("/notes", json=payload)

    response = client.get("/notes?keyword=uniquekeyword9876")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_search_notes_with_owner():
    payload = {
        "title": "Owner filtered note",
        "content": "Some content to search for ownerfilter42",
        "owner": "specificowner",
    }
    client.post("/notes", json=payload)

    response = client.get("/notes?keyword=ownerfilter42&owner=specificowner")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_delete_note():
    payload = {"title": "Delete me now", "content": "This will be deleted soon", "owner": "deleter"}
    created = client.post("/notes", json=payload)
    note_id = created.json()["id"]

    delete_response = client.delete(f"/notes/{note_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    get_response = client.get(f"/notes/{note_id}")
    assert get_response.status_code == 404


def test_delete_note_not_found():
    response = client.delete("/notes/999999")
    assert response.status_code == 404


def test_login_unauthenticated():
    response = client.post("/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 200
    assert response.json()["authenticated"] is False


def test_calculator_addition():
    response = client.post("/calculate", json={"expression": "1 + 2"})
    assert response.status_code == 200
    assert response.json()["result"] == 3


def test_calculator_complex_expression():
    response = client.post("/calculate", json={"expression": "10 * 2 + 5"})
    assert response.status_code == 200
    assert response.json()["result"] == 25


def test_calculator_division():
    response = client.post("/calculate", json={"expression": "10 / 4"})
    assert response.status_code == 200
    assert response.json()["result"] == 2.5


def test_calculator_negative():
    response = client.post("/calculate", json={"expression": "-5 + 3"})
    assert response.status_code == 200
    assert response.json()["result"] == -2


def test_calculator_invalid_expression():
    response = client.post("/calculate", json={"expression": "__import__('os')"})
    assert response.status_code == 400


def test_calculator_division_by_zero():
    response = client.post("/calculate", json={"expression": "1 / 0"})
    assert response.status_code == 400


def test_ratio_valid():
    response = client.get("/ratio?total=10&count=2")
    assert response.status_code == 200
    assert response.json()["ratio"] == 5.0


def test_ratio_zero_count():
    response = client.get("/ratio?total=10&count=0")
    assert response.status_code == 400


def test_note_score():
    payload = {"title": "Score this note", "content": "Content to score here", "owner": "scorer"}
    created = client.post("/notes", json=payload)
    note_id = created.json()["id"]

    response = client.get(f"/notes/{note_id}/score")
    assert response.status_code == 200
    assert "score" in response.json()
    assert response.json()["note_id"] == note_id


def test_note_score_not_found():
    response = client.get("/notes/999999/score")
    assert response.status_code == 404
