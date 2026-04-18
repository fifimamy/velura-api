danger_keywords = [
    " i want to die"," i am going to kill myself", "end my life", "i can't go on",
    "i want to end it all", "i can't take this anymore" 
    ]

danger_requests = [
    "do i have", "am i sick", "diagnose me", "what disease", "what illness",
    "how to cure", "treatment for", "symptoms of", "medical advice"
    ]

def is_dangerous(text):
    text = text.lower()
    for phrase in danger_keywords:
        if phrase in text:
            return True
    return False

def is_dangerous_request(text):
    text = text.lower()
    for phrase in danger_requests:
        if phrase in text:
            return True
    return False