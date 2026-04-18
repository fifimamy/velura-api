
from system.analysa import Manual_user_filter
from ai.semantic_analyzer import analyze_user_semantics , analyze_user_samantics2

RISK_LABELS = {
    0: "Safe",
    1: "Sensitive",
    2: "Potential Risk",
    3: "High Risk"
}

TYPE_LABELS = {
    0: "Medical Inquiry",
    1: "Symptom Report",
    2: "Psychological",
    3: "Emergency situations",
    4: "Related to self-harm",
    5: "Attempted boundary violation",
    6: "User's medical information",
    7: "Out of context"
}

def final_classification(answer):
    manual = Manual_user_filter(answer)
    semantic = analyze_user_semantics(answer)
    reson = analyze_user_samantics2(answer)

    return {
        "manual": manual,
        "semantic": RISK_LABELS.get(semantic),
        "reson": TYPE_LABELS.get(reson)
    }


def Verification(ai_classification):
    rate = ai_classification.get("Safe" , "Sensitive" , "Potential Risk" , "High Risk")