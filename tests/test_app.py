from fastapi.testclient import TestClient
from app import app, evaluate, SCHEMES
client = TestClient(app)
def test_health():
    assert client.get("/api/health").json()["status"] == "ok"
def test_missing():
    assert evaluate({}, SCHEMES[0])["status"] == "needs_information"
def test_mismatch():
    assert evaluate({"farmer": False}, SCHEMES[0])["status"] == "not_eligible"
def test_possible_kcc():
    assert evaluate({"farmer": True}, SCHEMES[1])["status"] == "potentially_eligible"
def test_question():
    assert client.post("/api/chat", json={"profile": {}, "focus": "pmkisan"}).json()["question_field"] is not None
def test_bad_income():
    assert evaluate({"urban": True, "annual_household_income": "many", "owns_pucca_house": False}, SCHEMES[2])["status"] == "needs_information"
def test_sources():
    assert all(s["source"].startswith("https://www.myscheme.gov.in/") for s in SCHEMES)
def test_route():
    assert client.get("/").status_code == 200
