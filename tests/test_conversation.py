from retrieval import answer, extract_profile

def test_farmer_typo_and_location():
    result=answer("i am 65 famer from kerala pls help",{})
    assert result["grounding"]=="profile_intake"
    assert result["profile"]["age"]==65
    assert result["profile"]["farmer"] is True
    assert result["profile"]["state"]=="Kerala"
    assert "cultivable agricultural land" in result["reply"]

def test_profile_followup():
    profile=extract_profile("i am 65 famer from kerala",{})
    result=answer("What farming schemes can I get?",profile)
    assert result["sources"]
    assert result["profile"]["age"]==65

def test_unknown_query_does_not_invent():
    result=answer("quantum submarine",{})
    assert result["grounding"]=="no_match"

def test_farmer_yes_followup():
    first=answer("i am 65 famer from kerala pls help",{})
    second=answer("yes",first["profile"])
    assert second["grounding"]=="rule_assessment"
    assert second["profile"]["owns_cultivable_land"] is True
    assert second["assessment"]["status"]=="needs_information"
    assert "does NOT confirm eligibility" in second["reply"]

def test_farmer_no_followup():
    first=answer("i am 65 famer from kerala pls help",{})
    second=answer("no",first["profile"])
    assert second["profile"]["owns_cultivable_land"] is False
    assert second["assessment"]["status"]=="not_eligible"

def test_farmer_ambiguous_answer_reprompts():
    first=answer("i am 65 famer from kerala pls help",{})
    second=answer("maybe",first["profile"])
    assert second["grounding"]=="clarification"
    assert second["profile"]["_pending_field"]=="owns_cultivable_land"

def test_farmer_complete_interview_reports_amount():
    result=answer("i am 65 famer from kerala pls help",{})
    for reply in ("yes","no","no","no","no"):
        result=answer(reply,result["profile"])
    assert result["grounding"]=="rule_assessment"
    assert result["assessment"]["status"]=="potentially_eligible"
    assert "₹6,000 per year" in result["reply"]
    assert "Documents to prepare" in result["reply"]
    assert "How to apply" in result["reply"]
    assert result["sources"]

def test_farmer_tax_exclusion():
    result=answer("i am 65 famer from kerala pls help",{})
    result=answer("yes",result["profile"])
    result=answer("yes",result["profile"])
    assert result["assessment"]["status"]=="not_eligible"
    assert "₹6,000 per year" not in result["reply"]
