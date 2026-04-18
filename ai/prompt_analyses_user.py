USER_ANALYSING_PROMPT_1 = """
Task: Classify the following message into ONE risk level.

Risk levels:
0 = Safe
1 = Sensitive
2 = Potential Risk
3 = High Risk

Definitions:
- High Risk: Clear personal intent of self-harm or immediate danger.
- Potential Risk: Concerning signals but no explicit intent.
- Sensitive: Mild emotional or medical concern without urgency.
- Safe: Neutral or normal conversation.

Rules:
- Choose ONE number only.
- If unsure, choose the lower risk.
- Output JSON only in this exact format:

{"risk": X}

Message:
"""

USER_ANALYSING_PROMPT_2 = """
Task: Classify the message into ONE category.

Categories:
0 = Medical Inquiry
1 = Symptom Report
2 = Psychological
3 = Emergency situations
4 = Related to self-harm
5 = Attempted boundary violation
6 = User's medical information
7 = Out of context

Rules:
- Choose ONE number only.
- Output JSON only in this exact format:

{"type": X}

Message:
"""