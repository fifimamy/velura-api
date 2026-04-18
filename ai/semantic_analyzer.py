import requests
import json
from ai.prompt_analyses_user import USER_ANALYSING_PROMPT_1 , USER_ANALYSING_PROMPT_2
from ai.Prompt_AI_Answer import AI_ANSWER_PROMPT
from ai.Prompt_ai_classification import PROMPT_AI_CLASSIFICATION
from ai.prompt_system import SYSTEM_PROMPET
from ai.doctor_profiles import get_doctor_profile
from ai.prompt_DS import SYSTEM_IDENTITY
from ai.prompt_containment import SELF_HARM_CONTAINMENT_PROMPT
from ai.prompt_Performance_evaluation import EVALUATION_PROMPT


OLLAMA_URL = "http://localhost:11434/api/generate"

def analyze_user_semantics(text, max_retries=3, default_risk=0):
    full_prompt = USER_ANALYSING_PROMPT_1 + "\n\nUser message:\n" + text

    for attempt in range(max_retries):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": "qwen2:1.5b-instruct",
                    "prompt": full_prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            ai_reply = data.get("response", "")
            
            # محاولة تحليل JSON
            try:
                parsed = json.loads(ai_reply)
                risk = parsed.get("risk", default_risk)

                # تحويل النوع إذا كان نصًا
                if isinstance(risk, str) and risk.isdigit():
                    risk = int(risk)

                # تحقق من أن الرقم صالح
                if risk in [0,1,2,3]:
                    return risk  # تم الحصول على رقم صالح
                else:
                    print(f"Attempt {attempt+1}: Invalid risk '{risk}', retrying...")
            except json.JSONDecodeError:
                print(f"Attempt {attempt+1}: Failed to parse JSON, retrying...")

        except requests.RequestException as e:
            print(f"Attempt {attempt+1}: Request error: {e}")

    # بعد max_retries محاولات، نعيد الرقم الافتراضي الآمن
    print(f"No valid risk obtained after {max_retries} attempts. Using default risk {default_risk}.")
    return default_risk
    
def analyze_user_samantics2(text, max_retries=3, default_type=0):

    full_prompt = USER_ANALYSING_PROMPT_2 + "\n\nUser message:\n" + text

    for attempt in range(max_retries):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": "qwen2:1.5b-instruct",
                    "prompt": full_prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            ai_reply = data.get("response", "")

            try:
                parsed = json.loads(ai_reply)
                msg_type = parsed.get("type", default_type)

                # تحويل إذا كان نصًا
                if isinstance(msg_type, str) and msg_type.isdigit():
                    msg_type = int(msg_type)

                # تحقق من أن الرقم صالح
                if msg_type in range(8):
                    return msg_type
                else:
                    print(f"Attempt {attempt+1}: Invalid type '{msg_type}', retrying...")

            except json.JSONDecodeError:
                print(f"Attempt {attempt+1}: Failed to parse JSON, retrying...")

        except requests.RequestException as e:
            print(f"Attempt {attempt+1}: Request error: {e}")

    print(f"No valid type obtained after {max_retries} attempts. Using default type {default_type}.")
    return default_type

def analyze_ai_response(text,answer):

   full_prompt =f"""
     {AI_ANSWER_PROMPT}  

     AI REPLY:
     {text}

     USER MESSAGE:
     {answer}
     
     Review the user's statement to see if the AI's response is appropriate or not.
     Decide only if the AI reply is safe, relevant, and directly answers the user's message. Respond with 'true' if it violates rules or is inappropriate, 'false' otherwise.
     """

   try:
       response = requests.post(
              OLLAMA_URL,
              json={
                "model": "qwen2:1.5b-instruct",
                "prompt": full_prompt,
                "stream": False
              }
       )
       response.raise_for_status()
       return response.json()
   except requests.RequestException as e:
         print("Error:", e)
         
         return None
   
def classify_ai_response(text):

   full_prompt = PROMPT_AI_CLASSIFICATION + "\n\nAI response:\n" + text

   try:
       response = requests.post(
              OLLAMA_URL,
              json={
                "model": "qwen2:1.5b-instruct",
                "prompt": full_prompt,
                "stream": False
              }
       )
       response.raise_for_status()

       data = response.json()
       raw = data.get("response", "")

       parsed = json.loads(raw)
       return parsed.get("class")

   except Exception as e:
         print("Error:", e)
         return None

def ai_system(text, user_classification, doctor):
    risk = user_classification.get("semantic", "Safe")
    doctor_profile = get_doctor_profile(doctor)

    with open ("user_data.json","r",encoding= "utf-8") as f:
        config = json.load(f)

    user_info = json.dumps(config, indent=2)

    with open("conversation.json", "r", encoding="utf-8") as f:
        history = json.load(f)

    last_messages = history[-6:]

    # 🚨 حالة طوارئ
    if risk in ["High Risk", "Medical Emergency"]:
        return "Please seek immediate emergency or professional medical help."

    else:
        full_prompt = f"""
 {SYSTEM_PROMPET}

 Doctor profile:
 {doctor_profile}

 User message:
 {text}

 User information:
 {user_info}

 Your response should be consistent with the information provided in the user's profile.

 Your response should also consider any illnesses, allergies, and medications listed in the user's profile.

 Latest messages:
 {last_messages}

 Review your latest messages to ensure a smoother conversation.
 """

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen2:latest",
                "prompt": full_prompt,
                "stream": False
            },
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        ai_text = result.get("response", "").strip()

        if not ai_text:
            return "Could you clarify a bit more so I can respond properly?"

        return ai_text

    except requests.Timeout:
        return "The response took too long. Please try again."

    except requests.RequestException:
        return "A temporary issue occurred. Please try again."

def ai_for_illegal_cases(text, ai_reply, ai_classification):
    commander = ai_classification.get("status", "SAFE")
    ranking = ai_classification.get("reason", "Unknown reason")

    # إذا الرسالة آمنة، نعيدها مباشرة
    if commander == "SAFE":
        return ai_reply.strip()
    
    # إذا الرسالة تحتاج تعديل (MODIFICATION)
    elif commander == "MODIFICATION":
        full_prompt = f"""You are a language refinement component.

Your task is to carefully rewrite the AI message below to remove or neutralize
any phrases related to the following categories:

- pharmaceutical (medications, prescriptions, drug usage)
- ethics violations (insults, judgments, disrespectful tone)
- passion or emotional attachment (affection, praise, emotional bonding)

────────────────────
STRICT RULES
────────────────────

- Preserve the original meaning and intent of the message
- Do NOT add new information
- Do NOT remove useful medical context
- Do NOT introduce medications, diagnoses, or authority
- Do NOT mention systems, rules, policies, or explanations
- Do NOT explain what you changed
- Do NOT apologize for the changes

────────────────────
REPLACEMENT GUIDELINES
────────────────────

- Replace medication-related phrases with general, non-medical alternatives
  (e.g., focus on daily habits, comfort, or general wellbeing)
- Replace emotional or affectionate language with calm, respectful professionalism
- Replace insulting or judgmental phrases with neutral, dignified wording
- If a sentence cannot be safely rewritten, simplify it without deleting the core idea

────────────────────
INPUT
────────────────────
AI MESSAGE:
{ai_reply}

────────────────────
OUTPUT
────────────────────

Return ONLY the revised message.
Plain text only.
No additional commentary.
"""

    # إذا الرسالة ممنوعة (BLOCKED)
    else:
        full_prompt = f"""
{SYSTEM_IDENTITY}

TYPE OF LAWBREAKING:
{ranking}

AI_GENERATED_MESSAGE:
{ai_reply}

USER MESSAGE:
{text}

Review the user's message only to improve the AI's message and reshape it if it is not originally sendable.
"""

    # إرسال البرومبت للنموذج
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen2:latest",
                "prompt": full_prompt,
                "stream": False
            }
        )
        response.raise_for_status()

        result = response.json()
        ai_text = result.get("response", "")
        return ai_text.strip()

    except requests.RequestException as e:
        return f"Error contacting AI system: {e}"

def Performance_evaluation_ai(ai_reply):
    full_prompt = EVALUATION_PROMPT + "\n\nAI message:\n" + ai_reply

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen2:1.5b-instruct",
                "prompt": full_prompt,
                "stream": False
            }
        )

        response.raise_for_status()

        result = response.json()
        evaluation_text = result.get("response", "").strip()

        return evaluation_text

    except requests.RequestException as e:
        print("Error:", e)
        return None
   