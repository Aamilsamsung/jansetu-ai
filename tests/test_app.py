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

def test_professional_exclusion_explained():
    profile={"farmer":True,"owns_cultivable_land":True,"excluded_professional":True}
    data=client.post("/api/chat",json={"profile":profile,"focus":"pmkisan"}).json()
    assert data["question_field"] is None
    assert "NOT ELIGIBLE" in data["reply"]
    assert "excluded-professional" not in data["reply"]
    assert "practising registered professional" in data["reply"]

def test_pmkisan_eligible_summary():
    profile={"farmer":True,"owns_cultivable_land":True,"income_tax_payer":False,
             "excluded_public_office":False,"excluded_government_employment":False,
             "excluded_professional":False}
    data=client.post("/api/chat",json={"profile":profile,"focus":"pmkisan"}).json()
    assert "POTENTIALLY ELIGIBLE" in data["reply"]
    assert "₹6,000" in data["reply"]
    assert "How to apply" in data["reply"]
