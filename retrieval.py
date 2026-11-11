import re
from app import SCHEMES, evaluate

ALIASES={"farmer":"agriculture kisan crop farming land kcc","student":"education scholarship college","hospital":"health ayushman pmjay medical","ration":"food nfsa pmgkay","house":"housing awas pucca urban pmay","loan":"credit kisan bank","apply":"application steps documents","eligible":"eligibility criteria"}
STOP={"what","which","how","the","for","and","are","can","get","does","this","that","with","about","tell","me","is","a","i","my","to","in","of","do","you","please","scheme","schemes","government"}
def terms(s):
    words=set(re.findall(r"[a-z0-9]+",s.lower()))-STOP
    out=set(words)
    for word in words:
        out.update(ALIASES.get(word,"").split())
    return out
def extract_profile(message, profile):
    updated=dict(profile)
    normalized=message.lower()
    age=re.search(r"\b(?:i am|i'm|age(?:d)?|years? old)\s*(\d{1,3})\b|\b(\d{1,3})\s*(?:years? old|yr old)\b",normalized)
    if age:
        value=int(next(v for v in age.groups() if v))
        if 0 < value < 120: updated["age"]=value
    if re.search(r"\b(?:farmer|famer|farmar|farming|agriculturist)\b",normalized):
        updated["farmer"]=True
    if re.search(r"\bkerala\b",normalized): updated["state"]="Kerala"
    if re.search(r"\b(?:karnataka|tamil nadu|maharashtra)\b",normalized):
        updated["state"]=re.search(r"\b(karnataka|tamil nadu|maharashtra)\b",normalized).group(1).title()
    return updated

def answer(message,profile):
    profile=extract_profile(message,profile)
    normalized=message.strip().lower()
    pending=profile.pop("_pending_field",None)
    if pending=="owns_cultivable_land":
        yes={"yes","y","yeah","yep","haan","ha","true","i do","yes i do","yes i own","yes i have"}
        no={"no","n","nope","nah","false","i don't","i do not","no i don't"}
        if normalized in yes or normalized.startswith(("yes ","yeah ","i own ","i have ")):
            profile["owns_cultivable_land"]=True
        elif normalized in no or normalized.startswith(("no ","i don't own ","i do not own ")):
            profile["owns_cultivable_land"]=False
        else:
            profile["_pending_field"]=pending
            return {"reply":"Please answer yes or no: do you own cultivable agricultural land?","sources":[],"matches":[],"grounding":"clarification","profile":profile}
    if profile.get("farmer") and "owns_cultivable_land" not in profile:
        profile["_pending_field"]="owns_cultivable_land"
        details=[]
        if profile.get("age"): details.append(str(profile["age"])+" years old")
        details.append("a farmer")
        if profile.get("state"): details.append("from "+profile["state"])
        return {"reply":"I understand you're "+", ".join(details)+". Do you own cultivable agricultural land? I will use your answer to check farming schemes, but further eligibility conditions may apply.","sources":["https://www.myscheme.gov.in/hi/schemes/pm-kisan"],"matches":["pmkisan","kcc"],"grounding":"profile_intake","profile":profile}
    if pending=="owns_cultivable_land" and "owns_cultivable_land" in profile:
        scheme=next(s for s in SCHEMES if s["id"]=="pmkisan")
        result=evaluate(profile,scheme)
        if result["status"]=="not_eligible":
            reply="Based on your answer, you do not meet the landholding condition in our preliminary PM-KISAN check. Other agricultural credit schemes may have different rules."
        else:
            reply="Thanks. You meet the landholding condition for the preliminary PM-KISAN check, but this does NOT confirm eligibility. We still need to check exclusions, including income tax and certain employment or professional categories."
        return {"reply":reply+" Official scheme information: "+scheme["source"],"sources":[scheme["source"]],"matches":["pmkisan","kcc"],"grounding":"rule_assessment","assessment":result,"profile":profile}
    query=terms(message)
    if profile.get("farmer"): query.update({"farmer","agriculture","kisan","crop","farming","land","kcc"})
    ranked=[]
    for scheme in SCHEMES:
        text=" ".join([scheme["name"],scheme["category"],scheme["benefit"]," ".join(scheme["documents"])," ".join(scheme["steps"])," ".join(r["field"].replace("_"," ") for r in scheme["rules"])])
        score=len(query & terms(text))
        if score: ranked.append((score,scheme))
    ranked.sort(key=lambda row:(-row[0],row[1]["name"]))
    matches=[s for _,s in ranked[:3]]
    if not matches:
        return {"reply":"I don't have verified information about that in my current scheme database, so I won't guess. Please check myscheme.gov.in.","sources":[],"matches":[],"grounding":"no_match","profile":profile}
    replies=[]
    for scheme in matches:
        status=evaluate(profile,scheme)
        if query & {"documents","document","papers","paper"}:
            detail="Documents: "+"; ".join(scheme["documents"])
        elif query & {"apply","application","register","steps"}:
            detail="Application steps: "+"; ".join(scheme["steps"])
        elif query & {"eligible","eligibility","qualify","why"}:
            detail="Preliminary status: "+status["status"].replace("_"," ")+". Missing: "+(", ".join(status["missing"]) or "none")+". Mismatches: "+(", ".join(status["failed"]) or "none")
        else:
            detail=scheme["benefit"]+" Preliminary status: "+status["status"].replace("_"," ")+"."
        replies.append(scheme["name"]+": "+detail+" Official source: "+scheme["source"])
    return {"reply":"\n\n".join(replies)+"\n\nUnofficial preliminary guidance only. Verify current rules on the official pages.","sources":[s["source"] for s in matches],"matches":[s["id"] for s in matches],"grounding":"curated_records","profile":profile}
