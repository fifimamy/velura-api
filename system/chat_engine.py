from threading import Thread
from system.user_filter import final_classification
from ai.ai_filter import final_classification_ai, evaluation
from ai.semantic_analyzer import ai_system, ai_for_illegal_cases, title_creation, capture_user_medical_summary, save_ai_evaluation_to_firebase
from system.storage import append_chat_exchange, stor_ai_evaluation


def _start_summary_capture(message, user_id, user_data):
    def worker():
        try:
            capture_user_medical_summary(user_id, message, user_data)
        except Exception as exc:
            print("Summary capture background error:", exc)

    thread = Thread(target=worker, daemon=True)
    thread.start()


def process_chat(message, doctor_type, chat_history, user_data, user_id=None,image_base64=None, language=None):

    print("USER:", repr(user_id))
    print("HAS IMAGE:", image_base64 is not None)
    print("LANGUAGE:", repr(language))
    
    user_result = final_classification(message)

    ai_reply = ai_system(message, user_result, doctor_type, chat_history, user_data, image_base64=image_base64, language=language)

    print("AI REPLY:", ai_reply)

    append_chat_exchange(message, ai_reply)

    # Capture medical summary details for later notification handling.
    if user_id:
        _start_summary_capture(message, user_id, user_data)

    evalu = evaluation(message, ai_reply)
    stor_ai_evaluation(evalu)

    if user_id:
        save_ai_evaluation_to_firebase(user_id, evalu)

    title = None
    if chat_history and len(chat_history) == 1:
        # use both the first (previous) message and the current message to create the title
        first_msg = chat_history[0]
        if isinstance(first_msg, dict):
            first_text = first_msg.get('text', '')
        else:
            first_text = str(first_msg)

        second_text = message or ''
        title_input = (first_text + "\n" + second_text).strip()
        if title_input:
            title = title_creation(title_input)

    return {
        "reply": ai_reply,
        "classification": user_result,
        "evaluation": evalu,
        "title": title
    }
