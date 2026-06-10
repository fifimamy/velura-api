
from ai.semantic_analyzer import analyze_ai_response 
from ai.semantic_analyzer import classify_ai_response 
from ai.semantic_analyzer import evaluate_ai_reply
from system.analysa import Manual_ai_filter
import json
import re

AI_CLASS_LABELS = {
    0: "UNSAFE",
    1: "SAFE"
}

def filter_1(ai_reply):
    return Manual_ai_filter(ai_reply)  


def filter_2(ai_reply, user_message):
    try:
        analysis = analyze_ai_response(ai_reply, user_message)
        raw = analysis.get("response", "")

        try:
            parsed = json.loads(raw)
            decision = parsed.get("class")
        except:
            decision = None

        # UNSAFE
        if decision == 0:
            return {
                "violation": True,
                "reason": "Model flagged unsafe"
            }

        # SAFE
        if decision == 1:
            return {
                "violation": False,
                "reason": None
            }

    except Exception as e:
        return {
            "violation": False,
            "reason": f"error: {e}"
        }

def final_classification_ai(ai_reply, user_message):
    manual_result = filter_1(ai_reply)
    ai_result = filter_2(ai_reply, user_message) or {
        "violation": False,
        "reason": None
    }

    forbidden_tags = [
        "Diagnosis_response",
        "The role",
        "system",
        "damage"
    ]

    # UNSAFE
    if (
        isinstance(manual_result, list)
        and any(tag in manual_result for tag in forbidden_tags)
    ) or ai_result["violation"]:

        return {
            "status": "UNSAFE",
            "reason": ai_result.get("reason") or manual_result
        }

    # SAFE
    return {
        "status": "SAFE",
        "output": ai_reply
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
    return evaluate_ai_reply(answer, ai_reply)
