
from ai.semantic_analyzer import analyze_ai_response 
from ai.semantic_analyzer import classify_ai_response 
from system.analysa import Manual_ai_filter
from system.user_masseg import user_masseg
from ai.semantic_analyzer import Performance_evaluation_ai
import json
import re

AI_CLASS_LABELS = {
    0: "FORBIDDEN",
    1: "SOFT_VIOLATION",
    2: "META_LEAK",
    3: "SAFE"
}
 
answer = user_masseg().strip()

def filter_1(ai_reply):
    return Manual_ai_filter(ai_reply)  


def filter_2(ai_reply):

  try:
    analysis = analyze_ai_response(ai_reply,answer)
    raw = analysis.get("response", "")

    try:
        parsed = json.loads(raw)
        decision = parsed.get("class")
    except:
     decision = None

    if decision == 1:
        classification = classify_ai_response(ai_reply)
        return {
            "violation": True,
            "reason": AI_CLASS_LABELS.get(classification)
        }

    if decision == 0:  
        return{
           "violation": False,
           "reason": None
        }
    

  except Exception as e:
       return {
            "violation": False,
            "reason": f"error: {e}"
        }
    

def final_classification_ai(ai_reply):
    manual_result = filter_1(ai_reply)
    ai_result = filter_2(ai_reply) or {"violation": False, "reason": None}

    high_risk_tags = ["Diagnosis_response", "The role", "system", "damage"]
    soft_tags = ["pharmaceutical", "Ethics", "Passion"]

    # 🚫 BLOCKED
    if (
        (isinstance(manual_result, list) and any(tag in manual_result for tag in high_risk_tags))
        or ai_result["violation"] is True and ai_result["reason"] == "FORBIDDEN"
    ):
        return {
            "status": "BLOCKED",
            "reason": ai_result["reason"] or manual_result
        }

    # ⚠️ MODIFICATION
    if (
        (isinstance(manual_result, list) and any(tag in manual_result for tag in soft_tags))
        or ai_result["violation"] is True and ai_result["reason"] in ["SOFT_VIOLATION", "META_LEAK"]
    ):
        return {
            "status": "MODIFICATION",
            "reason": ai_result["reason"] or manual_result
        }

    # ✅ SAFE
    if manual_result == "SAFE" and ai_result["violation"] is False:
        return {
            "status": "SAFE",
            "output": ai_reply
        }

    # fallback أمني
    return {
        "status": "MODIFICATION",
        "reason": "Uncertain state"
    }


def extract_score(text):
    match = re.search(r"[012]", text)
    if match:
        return int(match.group())
    return 1

AI_EVALUATION =  {
    0: "Low confidence",
    1: "Medium confidence",
    2: "High confidence"
}

def evaluation(answer, ai_reply):

    evaluation_text = Performance_evaluation_ai(ai_reply)

    score = extract_score(evaluation_text)

    return {
        "user_message": answer,
        "ai_reply": ai_reply,
        "confidence_score": score,
        "evaluation": AI_EVALUATION.get(score)
    }
