from urllib import response

from ai.Prompts import DUPLICATE_DETECTOR,CLASSIFYING_IMPORTANT,RESUME_IMPORTANT,USER_INFO_IMPORTANT,CONVERSATION_RULES,IMAGE_PROMPT, TITLE_GENERATION_PROMPT, SYSTEM_IDENTITY, SYSTEM_BEHAVIOR, SYSTEM_SAFETY, SELF_HARM_GUIDED_PROMPT,EMERGENCY_GUIDED_PROMPT, REFINER_BEHAVIOR,REFINER_IDENTITY,REFINER_RULES,REFINER_SAFETY
import requests
import os


def _language_instruction(language):
    if not language:
        return ""

    normalized = language.strip().lower()
    if normalized.startswith("ar"):
        return "Respond in Arabic."
    if normalized.startswith("en"):
        return "Respond in English."

    return ""


def _format_image_context(image_analysis):
    if not image_analysis:
        return ""

    return f"""
    IMAGE ANALYSIS:
    {image_analysis}

    The user has provided an image.
    Use this visual analysis when answering any question related to the image, visible symptoms, wounds, skin issues, or other visual clues.
    If the user's message refers to the image or to something they showed, the response must incorporate this image analysis.
    If the user asks about a body part, symptom, lesion, rash, or visible sign, include at least one observation from the image analysis.
    If the user does not explicitly mention the image, you may still use the visual information when it is relevant to the medical question.
    Do not ignore the image analysis.
    Do not assume the analysis is fully accurate.
    Always consider the possibility of errors in the image analysis.
    """

def generate_standard_response(text,doctor_profile,user_info, language=None,image_analysis=None, chat_history=None):
    language_instruction = _language_instruction(language)

    image_context = _format_image_context(image_analysis)

    full_prompt = f"""
 {SYSTEM_IDENTITY}

 {SYSTEM_BEHAVIOR}

 {CONVERSATION_RULES}

 {SYSTEM_SAFETY}

 {language_instruction}

 Never welcome a user unless they welcome you first.

 SPECIALTY:
 {doctor_profile}
 Stay strictly within this specialty lens.
 Do not drift into unrelated systems.
 
 
 KNOWN USER DATA:
 {user_info}

 This information is already known.
 Never ask again about:
 - age
 - gender
 - allergies
 - illnesses
 - medications
 if they already exist above.


 Do not change username; always write it in Latin characters.

 {image_context}

 If an image analysis is provided, use it in your response and make sure any image-related details come from this analysis.
 If the response is related to the image, mention at least one visible detail from the image analysis.
 Do not repeat the USER MESSAGE text in your final reply.
 Do not prefix your response with 'Velura:' or similar labels.

  CONVERSATION HISTORY:
 {chat_history}

 The conversation history is ordered from oldest to newest.

 The most recent user message is the USER MESSAGE section below.

 Use the conversation history only as context.

 Do not answer previous questions again.

 If the user asks a follow-up question,
 continue from the current topic.

 Do not restart the explanation from the beginning.

 Do not repeat information already explained in recent messages.

 USER MESSAGE:
 {text}


 Your response should be consistent with the information provided in the user's profile.

 Your response should also consider any illnesses, allergies, and medications listed in the user's profile.

 Review your latest messages to ensure a smoother conversation.

 Repeatedly greeting and introducing the user is strictly prohibited.
 """
    return query_model(full_prompt)


def generate_self_harm_response(text, language=None, image_analysis=None):
    language_instruction = _language_instruction(language)

    image_context = _format_image_context(image_analysis)

    full_prompt = f"""
    {SELF_HARM_GUIDED_PROMPT}

    {language_instruction}

    {image_context}

    If an image analysis is provided, use it when relevant to the user's message.
    If the user mentions the image or visible symptoms, include at least one visible detail from the image analysis.
    Do not repeat the USER MESSAGE text in your final reply.
    Do not prefix your response with 'Velura:' or similar labels.

    USER MESSAGE:
    {text}

    """

    return query_model(full_prompt)


def generate_emergency_response(text, language=None, image_analysis=None):
    language_instruction = _language_instruction(language)

    image_context = _format_image_context(image_analysis)

    full_prompt = f"""
    {EMERGENCY_GUIDED_PROMPT}

    {language_instruction}

    {image_context}

    If an image analysis is provided, use it when relevant to the user's message.
    If the user mentions the image or visible symptoms, include at least one visible detail from the image analysis.
    Do not repeat the USER MESSAGE text in your final reply.
    Do not prefix your response with 'Velura:' or similar labels.

    USER MESSAGE:
    {text}
    
    """

    return query_model(full_prompt)

def refine_response(text, ai_reply, user_data):
    full_prompt = f"""
 {REFINER_IDENTITY}

 {REFINER_BEHAVIOR}

 {REFINER_SAFETY}

 {REFINER_RULES}

 USER MESSAGE:
 {text}

 ORIGINAL RESPONSE:
 {ai_reply}

 USER PROFILE:
 {user_data}

 
 Review the original response and refine it to better align with the user's profile and the guidelines provided. Ensure that the refined response is safe, relevant, and consistent with the user's medical history and current condition.
 """

    return query_model(full_prompt)

def title_creator(text, language=None):
    full_prompt = f"""
 {TITLE_GENERATION_PROMPT}

 USER MESSAGE:
 {text}


    Generate a concise and relevant title for the user's message that captures the main topic or concern expressed in the message. The title should be informative and reflect the content of the user's message accurately.
 """

    return query_model(full_prompt)

def Image_captioner(image_base64):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "No API key"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro-vision:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": IMAGE_PROMPT
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        data = response.json()

        print("GEMINI IMAGE RESPONSE:", data)

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print("IMAGE ERROR:", e)
        return "Image analysis failed"

def classify_user_message(text):
    full_prompt = f"""
    {USER_INFO_IMPORTANT}
    USER MESSAGE:
    {text}
    """

    return query_model(full_prompt)

def resume_message(text):
    full_prompt = f"""
    {RESUME_IMPORTANT}
    USER MESSAGE:
    {text}
    """

    return query_model(full_prompt)

def classify_resume(text):
    full_prompt = f"""
    {CLASSIFYING_IMPORTANT}
    USER MESSAGE:
    {text}
    """

    return query_model(full_prompt)

def detect_duplicate(text, user_info, user_info2):
    full_prompt = f"""
    {DUPLICATE_DETECTOR}
    USERMEDICAL INFO:
    {user_info}
    {user_info2}
    NEW FACT:
    {text}
    """

    return query_model(full_prompt)

def query_model(prompt, model_name="gemini-1.0-pro"):
    api_key = os.getenv("GEMINI_API_KEY")

    print("API KEY START =", api_key[:10])

    if not api_key:
        return "ERROR: Missing API key"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }



    try:
        response = requests.post(url, json=payload, timeout=60)
        print(response.status_code)
        print(response.text)
        data = response.json()

        print("GEMINI RAW RESPONSE:", data)  # مهم جداً للتصحيح

        # ⛔ لا تسكت على الخطأ
        if "candidates" not in data:
            return f"ERROR_NO_CANDIDATES: {data}"

        if not data["candidates"]:
            return "ERROR_EMPTY_CANDIDATES"

        return data["candidates"][0]["content"]["parts"][0].get("text", "")


    except Exception as e:
        return f"ERROR_EXCEPTION: {str(e)}"
    