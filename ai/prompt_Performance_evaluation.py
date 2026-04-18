EVALUATION_PROMPT="""
After responding to the user, rate your confidence in the medical information provided.

Use only one of these three levels:

High: The information is clear, common, and based on established medical knowledge.

Moderate: The information may be correct, but obtaining more details from the user would help confirm it further.

Low: The condition is unclear, involves risks, or requires a specialist medical evaluation.

Enter your confidence level at the end like this:

0 = Low confidence
1 = Medium confidence
2 = High confidence

Choose only one number.
"""