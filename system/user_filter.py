
from system.analysa import Manual_user_filter
from ai.semantic_analyzer import analyze_user_semantics , analyze_user_samantics2

RISK_LABELS = {
    0: "Normal",
    1: "Critical"
}

TYPE_LABELS = {
    0: "Normal",
    1: "Psychological",
    2: "Emergency",
    3: "Self-harm"
}

def final_classification(answer):
    manual = Manual_user_filter(answer)
    semantic = analyze_user_semantics(answer)
    reason = analyze_user_samantics2(answer)

    return {
        "manual": manual,
        "semantic": RISK_LABELS.get(semantic),
        "reason": TYPE_LABELS.get(reason)
    }


def Verification(ai_classification):
    rate = ai_classification.get("Normal" , "Critical")