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

FARMER_FIELDS=[
 ("owns_cultivable_land","Do you own cultivable agricultural land?"),
 ("income_tax_payer","Does your farmer family pay income tax?"),
 ("excluded_public_office","Is anyone in your farmer family an excluded public-office holder?"),
 ("excluded_government_employment","Does your farmer family include a government employee or pensioner covered by PM-KISAN exclusions?"),
 ("excluded_professional","Does your farmer family include a practising registered professional covered by PM-KISAN exclusions?")
]
YES={"yes","y","yeah","yep","haan","true","i do","yes i do"}
NO={"no","n","nope","nah","false","i don't","i do not"}
def response(reply,profile,grounding,matches=None,assessment=None):
    result={"reply":reply,"profile":profile,"grounding":grounding,"matches":matches or [],"sources":[s["source"] for s in SCHEMES if s["id"] in (matches or [])]}
    if assessment is not None: result["assessment"]=assessment
    return result

def answer(message,profile):
    profile=extract_profile(message,profile)
    normalized=message.strip().lower()
    pending=profile.pop("_pending_field",None)
    if pending:
        yes=normalized in YES or normalized.startswith(("yes ","yeah ","i own ","i have "))
        no=normalized in NO or normalized.startswith(("no ","i don't own ","i do not own "))
        if not yes and not no:
            profile["_pending_field"]=pending
            question=next((q for field,q in FARMER_FIELDS if field==pending),"Please answer yes or no.")
            return response("Please answer yes or no. "+question,profile,"clarification",["pmkisan","kcc"])
        profile[pending]=yes
    if profile.get("farmer"):
        pmkisan=next(s for s in SCHEMES if s["id"]=="pmkisan")
        assessment=evaluate(profile,pmkisan)
        if assessment["status"]=="not_eligible":
            return response("PM-KISAN: our preliminary rule check found an exclusion or unmet condition ("+", ".join(assessment["failed"])+"). This does not determine eligibility for Kisan Credit Card, which depends on bank assessment. Official source: "+pmkisan["source"],profile,"rule_assessment",["pmkisan","kcc"],assessment)
        missing=next(((field,question) for field,question in FARMER_FIELDS if field not in profile),None)
        if missing:
            field,question=missing
            profile["_pending_field"]=field
            intro=""
            if pending=="owns_cultivable_land":
                intro="Thanks. You meet the landholding condition for the preliminary PM-KISAN check, but this does NOT confirm eligibility. "
            elif pending:
                intro="Thanks, I've recorded that answer. "
            else:
                details=[]
                if profile.get("age"): details.append(str(profile["age"])+" years old")
                details.append("a farmer")
                if profile.get("state"): details.append("from "+profile["state"])
                intro="I understand you're "+", ".join(details)+". "
            return response(intro+question,profile,"rule_assessment" if pending else "profile_intake",["pmkisan","kcc"],assessment)
        if assessment["status"]=="potentially_eligible":
            reply=("Preliminary result: you potentially qualify for PM-KISAN. The listed benefit is ₹6,000 per year, paid in three instalments, subject to official verification and exclusions. "
                   "Documents to prepare: "+", ".join(pmkisan["documents"])+". "
                   "How to apply: "+"; ".join(pmkisan["steps"])+". "
                   "Official source: "+pmkisan["source"]+". "
                   "Kisan Credit Card may also be relevant, but credit amount and approval depend on the bank. This is NOT government approval.")
            return response(reply,profile,"rule_assessment",["pmkisan","kcc"],assessment)
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
