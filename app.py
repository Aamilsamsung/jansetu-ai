from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
SCHEMES = json.loads((ROOT / "data" / "schemes.json").read_text(encoding="utf-8"))
app = FastAPI(title="JanSetu AI", version="0.2.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
QUESTIONS = {
    "farmer": "Are you a farmer?",
    "owns_cultivable_land": "Do you own cultivable agricultural land?",
    "income_tax_payer": "Does your farmer family pay income tax?",
    "excluded_public_office": "Is anyone in your farmer family an excluded public-office holder?",
    "excluded_government_employment": "Does your farmer family include a government employee or pensioner covered by exclusions?",
    "excluded_professional": "Does your farmer family include a practising registered professional?",
    "urban": "Do you live in an urban area?",
    "annual_household_income": "What is your household annual income in rupees?",
    "owns_pucca_house": "Does your family own a pucca house anywhere in India?",
    "nfsa_household": "Is your household a registered NFSA beneficiary?",
    "pmjay_verified_beneficiary": "Have you verified PM-JAY beneficiary status on the official system?",
}
class ProfileRequest(BaseModel):
    profile: dict = Field(default_factory=dict)
class ChatRequest(ProfileRequest):
    message: str = Field(default="", max_length=1000)
    focus: str | None = None

def evaluate(profile, scheme):
    missing, passed, failed = [], [], []
    for rule in scheme["rules"]:
        field, expected = rule["field"], rule["value"]
        actual = profile.get(field)
        if actual is None or actual == "":
            missing.append(field)
            continue
        if isinstance(expected, bool):
            if not isinstance(actual, bool):
                missing.append(field)
                continue
            valid = actual == expected
        elif rule["op"] == "lte":
            if isinstance(actual, bool) or not isinstance(actual, (int, float)) or actual < 0:
                missing.append(field)
                continue
            valid = actual <= expected
        else:
            valid = actual == expected
        (passed if valid else failed).append(field)
    status = "not_eligible" if failed else ("needs_information" if missing else "potentially_eligible")
    return {"status": status, "missing": missing, "passed": passed, "failed": failed}

@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "schemes": len(SCHEMES)}

@app.get("/api/schemes")
def list_schemes():
    return SCHEMES

@app.post("/api/check")
def check(req: ProfileRequest):
    return [{"scheme": scheme, "assessment": evaluate(req.profile, scheme)} for scheme in SCHEMES]

@app.post("/api/chat")
def chat(req: ChatRequest):
    results = [{"scheme": scheme, "assessment": evaluate(req.profile, scheme)} for scheme in SCHEMES]
    if req.focus:
        selected = [row for row in results if row["scheme"]["id"] == req.focus]
        if selected:
            results = selected
    if not results:
        return {"reply":"Scheme not found. Please select a listed scheme.","question_field":None,"results":[]}
    selected=results[0]
    assessment=selected["assessment"]
    scheme=selected["scheme"]
    readable=lambda field: QUESTIONS.get(field,field.replace("_"," "))
    if assessment["status"]=="not_eligible":
        reasons="; ".join(readable(field) for field in assessment["failed"])
        reply=(f"Preliminary result for {scheme['name']}: NOT ELIGIBLE based on the answers provided. "
               f"Unmet condition(s): {reasons}. "
               "If you answered incorrectly, reset and check again. "
               f"Official source: {scheme['source']}. This is not an official decision.")
        return {"reply":reply,"question_field":None,"results":results,"disclaimer":"Unofficial preliminary guidance; verify on the official government portal."}
    if assessment["status"]=="potentially_eligible":
        reply=(f"Preliminary result: POTENTIALLY ELIGIBLE for {scheme['name']}. "
               f"Listed benefit: {scheme['benefit']} "
               f"Documents: {'; '.join(scheme['documents'])}. "
               f"How to apply: {'; '.join(scheme['steps'])}. "
               f"Official source: {scheme['source']}. "
               "This is not approval; final eligibility is determined by the responsible authority.")
        return {"reply":reply,"question_field":None,"results":results,"disclaimer":"Unofficial preliminary guidance; verify on the official government portal."}
    priority = {"farmer": 0, "urban": 1, "nfsa_household": 2, "pmjay_verified_beneficiary": 3, "owns_cultivable_land": 4, "income_tax_payer": 5, "excluded_public_office": 6, "excluded_government_employment": 7, "excluded_professional": 8, "annual_household_income": 9}
    missing=sorted(assessment["missing"],key=lambda x:priority.get(x,20))
    field=missing[0]
    return {"reply":QUESTIONS.get(field,"Please provide: "+field.replace("_"," ")),
            "question_field":field,"results":results,
            "disclaimer":"Unofficial preliminary guidance; verify on the official government portal."}

@app.post("/api/ask")
def ask(req: ChatRequest):
    from retrieval import answer
    return answer(req.message,req.profile)
