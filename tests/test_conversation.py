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
