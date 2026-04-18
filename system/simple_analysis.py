KEYWORDS ={
    "anxiety": [
        "anxious",
        "anxiety",
        "panic",
        "fear"
    ],
    "sadness": [
        "sad",
        "depressed",
        "down"
    ],
    "fatigue": [
        "tired",
        "exhausted",
        "burned"
    ],
    "suicide": [
        "kill myself",
        " want to die",
        "end my life",
        " i want to die",
        " i am going to kill myself",
        "end my life", "i can't go on",
        "i want to end it all",
        "i can't take this anymore"
    ],

    "drugs": [
        "heroin",
        "cocaine",
        "meth",
        "addicted",
        "overdose",
        "Abused drugs",
        "Substance abuse",
        "Drug addiction"
    ],
    "diagnosis": [
        "do i have",
        "am i sick",
        "diagnose me",
        "what disease",
        "what illness",
        "how to cure",
        "treatment for",
        "symptoms of",
        "medical advice",
        "prescribe",
        "prescription"
    ],


    "Diagnosis_response" : [
        "You are infected with",
        "You have been diagnosed with",
        "The test results indicate",
        "The diagnosis is",
        "You are suffering from"
    ],
    "pharmaceutical": [
        "Use this medicine",
        "Take this drug",
        "Prescribe this medication",
        "Administer this pharmaceutical",
        "Medication dosage is"
    ],
    "Ethics": [
        "You are stupid",
        "I hate you",
        "You are worthless",
        "I don't care about you",
        "You are a failure",
        "You are a failure",
        "You are useless",
        "I despise you",
        "You are pathetic",
        "I loathe you"
    ],
    "Passion": [
        "I love you",
        "I appreciate you",
        "You are wonderful",
        "I cherish you",
        "You are fantastic",
        "I adore you",
        "You are incredible" 
    ],
    "The role": [
        "I am a doctor",
        "I am a physician",
        "I am a medical professional",
        "I am a healthcare provider",
        "I am a clinician"
    ],
    "damage": [
        "Try doing this physically",
        "Harm yourself by",
        "Injure yourself with",
        "Physically hurt yourself using",
        "Cause physical damage with",
        "Jump from a high place",
        "Cut yourself with",
        "Burn yourself using",
        "Shoot yourself with",
        "Poison yourself with"
    ],
    "System": [
        "As a linguistic model",
        "I was trained",
        "Policies",
        "Rules",
        "As a system",
        "Designed",
        "The rules I follow are",
        "I should respond to the user with",
        "The safe response for the user is"
    ]
}

def analyze_text(text):
    text = text.lower()

    for category, words in KEYWORDS.items():
        for word in words:
            if word.lower() in text:
                return category
            
    return "unknown"