from retrieval import answer
def test_no_invented_scheme():
    result=answer("quantum submarine submarine",{})
    assert result["grounding"]=="no_match" and result["sources"]==[]
def test_official_sources():
    result=answer("Kisan Credit Card loan",{"farmer":True})
    assert result["sources"] and all(url.startswith("https://www.myscheme.gov.in/") for url in result["sources"])
def test_rule_results():
    result=answer("Am I eligible for Kisan Credit Card loan?",{"farmer":False})
    assert "not eligible" in result["reply"]
