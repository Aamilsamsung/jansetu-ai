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
def answer(message,profile):
    query=terms(message)
    ranked=[]
    for scheme in SCHEMES:
        text=" ".join([scheme["name"],scheme["category"],scheme["benefit"]," ".join(scheme["documents"])," ".join(scheme["steps"])," ".join(r["field"].replace("_"," ") for r in scheme["rules"])])
        score=len(query & terms(text))
        if score: ranked.append((score,scheme))
    ranked.sort(key=lambda row:(-row[0],row[1]["name"]))
    matches=[s for _,s in ranked[:3]]
    if not matches:
        return {"reply":"I don't have verified information about that in my current scheme database, so I won't guess. Please check myscheme.gov.in.","sources":[],"matches":[],"grounding":"no_match"}
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
    return {"reply":"\n\n".join(replies)+"\n\nUnofficial preliminary guidance only. Verify current rules on the official pages.","sources":[s["source"] for s in matches],"matches":[s["id"] for s in matches],"grounding":"curated_records"}
