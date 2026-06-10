import os
import re
import time
import uuid
import requests
import json
import builtins
from ai.doctor_profiles import get_doctor_profile
from ai.notification_templates import build_notification_for_item
from ai.Prompts import USER_ANALYSING_PROMPT_1 , USER_ANALYSING_PROMPT_2,AI_ANSWER_PROMPT,PROMPT_AI_CLASSIFICATION,EVALUATION_PROMPT
from ai.responders import detect_duplicate,classify_resume,resume_message,classify_user_message,Image_captioner, refine_response, generate_emergency_response, generate_self_harm_response, generate_standard_response, title_creator
from system.medical_profile import user_information
from system.firebase import load_firebase_user, save_firebase_user, save_ai_evaluation_to_firebase


OLLAMA_URL = "http://localhost:11434/api/generate"


def _safe_json_loads(raw, default=None):
    if raw is None:
        return default
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return default


def _safe_int(value, default=None):
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return default
        return int(float(value))
    except Exception:
        return default


def safe_print(*args, **kwargs):
    builtins_print = builtins.print
    try:
        builtins_print(*args, **kwargs)
    except Exception:
        try:
            text = " ".join(str(a) for a in args)
            builtins_print(text, **{k: v for k, v in kwargs.items() if k in ('sep', 'end', 'file', 'flush')})
        except Exception:
            pass

print = safe_print


def _extract_json_from_text(raw_text):
    if not isinstance(raw_text, str):
        return None

    raw_text = raw_text.strip()
    json_match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
    if not json_match:
        return None

    json_text = json_match.group(0)

    try:
        return json.loads(json_text)
    except ValueError:
        try:
            cleaned = re.sub(r"([\t\n\r]+)", " ", json_text)
            return json.loads(cleaned)
        except ValueError:
            return None


def _parse_evaluation_number(text, keys):
    if not isinstance(text, str):
        return None

    for key in keys:
        # look for numeric values after key names
        regex = re.compile(rf"{re.escape(key)}\s*[:=]\s*([0-2])", flags=re.IGNORECASE)
        match = regex.search(text)
        if match:
            return int(match.group(1))

    # fallback on any standalone 0-2 in the text
    match = re.search(r"\b([0-2])\b", text)
    if match:
        return int(match.group(1))

    return None


def _parse_evaluation_label(text, keys):
    if not isinstance(text, str):
        return None

    for key in keys:
        regex = re.compile(rf"{re.escape(key)}\s*[:=]\s*(Low|Medium|High)", flags=re.IGNORECASE)
        match = regex.search(text)
        if match:
            label = match.group(1).capitalize()
            return label

    return None


def _normalize_label(score, fallback=None):
    if score == 0:
        return "Low"
    if score == 1:
        return "Medium"
    if score == 2:
        return "High"
    return fallback


def count_follow_up_requests(text):
    if not isinstance(text, str) or not text.strip():
        return 0

    lower = text.lower()
    patterns = [
        r"\bهل\b",
        r"من فضلك",
        r"الرجاء",
        r"يرجى",
        r"أخبرني",
        r"أخبريني",
        r"هل يمكنك",
        r"هل تستطيع",
        r"هل يمكن",
        r"ما هو",
        r"متى",
        r"أين",
        r"لماذا",
        r"كيف",
        r"كم",
        r"could you",
        r"can you",
        r"please",
        r"tell me",
        r"let me know",
    ]

    count = 0
    for pat in patterns:
        count += len(re.findall(pat, lower))

    question_marks = text.count("؟") + text.count("?")
    count = max(count, question_marks)

    return min(count, 10)


def _build_evaluation_prompt(user_message, ai_reply):
    return EVALUATION_PROMPT.format(
        user_message=user_message or "",
        ai_reply=ai_reply or ""
    )


def evaluate_ai_reply(user_message, ai_reply):
    evaluation_text = Performance_evaluation_ai(user_message, ai_reply)
    json_data = _extract_json_from_text(evaluation_text or "") or {}

    understanding_quality_score = json_data.get("understanding_quality")
    understanding_quality_label = json_data.get("understanding_quality_label")
    missing_information_score = json_data.get("missing_information")
    missing_information_label = json_data.get("missing_information_label")
    confidence_score = json_data.get("confidence")
    confidence_label = json_data.get("confidence_label")
    notes = json_data.get("notes") or json_data.get("note") or ""

    if understanding_quality_score is None:
        understanding_quality_score = _parse_evaluation_number(evaluation_text, ["understanding_quality", "understanding_quality_score", "understanding quality"])
    if understanding_quality_label is None:
        understanding_quality_label = _parse_evaluation_label(evaluation_text, ["understanding_quality_label", "understanding quality"])
    if missing_information_score is None:
        missing_information_score = _parse_evaluation_number(evaluation_text, ["missing_information", "missing_information_score", "missing information"])
    if missing_information_label is None:
        missing_information_label = _parse_evaluation_label(evaluation_text, ["missing_information_label", "missing information"])
    if confidence_score is None:
        confidence_score = _parse_evaluation_number(evaluation_text, ["confidence", "confidence_score"])
    if confidence_label is None:
        confidence_label = _parse_evaluation_label(evaluation_text, ["confidence_label", "confidence"])

    understanding_quality_score = _safe_int(understanding_quality_score, 1)
    missing_information_score = _safe_int(missing_information_score, 1)
    confidence_score = _safe_int(confidence_score, 1)
    understanding_quality_label = understanding_quality_label or _normalize_label(understanding_quality_score, "Medium")
    missing_information_label = missing_information_label or _normalize_label(missing_information_score, "Medium")
    confidence_label = confidence_label or _normalize_label(confidence_score, "Medium")

    response_text = ai_reply or ""
    response_length_chars = len(response_text)
    response_length_words = len(re.findall(r"\w+", response_text, flags=re.UNICODE))
    follow_up_requests = count_follow_up_requests(response_text)

    return {
        "user_message": user_message,
        "ai_reply": ai_reply,
        "understanding_quality_score": understanding_quality_score,
        "understanding_quality_label": understanding_quality_label,
        "missing_information_score": missing_information_score,
        "missing_information_label": missing_information_label,
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
        "response_length_chars": response_length_chars,
        "response_length_words": response_length_words,
        "follow_up_requests": follow_up_requests,
        "notes": notes,
        "raw_evaluation": evaluation_text,
        "evaluation": confidence_label,
    }


EXPIRATION_DAYS = {
    "temporary_short": 7,
    "temporary_medium": 30,
    "temporary_long": 180,
    "chronic": None,
    "allergy": None,
}


def _calculate_expiration(category):
    if category not in EXPIRATION_DAYS:
        return None

    days = EXPIRATION_DAYS.get(category)
    if days is None:
        return None

    return int(time.time()) + int(days * 24 * 60 * 60)


def _format_medical_info(user_profile):
    if not isinstance(user_profile, dict):
        return ""

    keys = [
        "name",
        "age",
        "gender",
        "height_cm",
        "weight_kg",
        "chronic_diseases",
        "allergies",
        "other_user_notes",
        "medical_conditions",
        "medications",
    ]

    lines = []
    for key in keys:
        value = user_profile.get(key)
        if value:
            lines.append(f"{key.replace('_', ' ').title()}: {value}")

    if not lines and user_profile:
        try:
            lines.append(json.dumps(user_profile, ensure_ascii=False))
        except Exception:
            lines.append(str(user_profile))

    return "\n".join(lines)


def _format_summary_history(summary_history):
    if not summary_history:
        return ""

    if isinstance(summary_history, dict):
        summary_history = [summary_history]
    elif isinstance(summary_history, str):
        summary_history = [summary_history]

    items = []
    for index, entry in enumerate(summary_history, start=1):
        if isinstance(entry, dict):
            text = entry.get("summary") or entry.get("important_info") or json.dumps(entry, ensure_ascii=False)
        else:
            text = str(entry)
        text = text.strip()
        if text:
            items.append(f"Previous summary {index}: {text}")

    return "\n".join(items)


def _normalize_summary_history(summary_history):
    if isinstance(summary_history, list):
        return [_normalize_summary_item(item) for item in summary_history]
    if isinstance(summary_history, dict):
        return [_normalize_summary_item(summary_history)]
    if isinstance(summary_history, str):
        return [_normalize_summary_item(summary_history)]
    return []


def _generate_summary_id():
    return str(uuid.uuid4())


def _normalize_summary_item(entry):
    if isinstance(entry, str):
        entry = {"important_info": entry}

    if not isinstance(entry, dict):
        return {
            "id": _generate_summary_id(),
            "important_info": str(entry),
            "summary": str(entry),
            "category": None,
            "created_at": int(time.time()),
            "expires_at": None,
            "status": "active",
            "notification_ready": False,
        }

    summary_text = entry.get("summary") or entry.get("important_info") or ""
    created_at = _parse_timestr(entry.get("created_at")) or int(time.time())
    expires_at = entry.get("expires_at")
    if expires_at is not None:
        expires_at = int(_parse_timestr(expires_at))

    normalized = {
        "id": entry.get("id") or _generate_summary_id(),
        "important_info": entry.get("important_info") or summary_text,
        "summary": summary_text,
        "category": entry.get("category"),
        "created_at": created_at,
        "expires_at": expires_at,
        "status": entry.get("status") or "active",
        "notification_ready": bool(entry.get("notification_ready", False)),
    }

    if entry.get("ended_at") is not None:
        normalized["ended_at"] = int(_parse_timestr(entry.get("ended_at")) or int(time.time()))
    if entry.get("label") is not None:
        normalized["label"] = entry.get("label")
    if entry.get("retention_seconds") is not None:
        normalized["retention_seconds"] = entry.get("retention_seconds")
    if entry.get("extended_at") is not None:
        normalized["extended_at"] = int(_parse_timestr(entry.get("extended_at")) or int(time.time()))
    if entry.get("extension_days") is not None:
        normalized["extension_days"] = entry.get("extension_days")

    # Optional follow-up timestamp (can be numeric timestamp or parseable string)
    if entry.get("follow_up_at") is not None:
        try:
            normalized["follow_up_at"] = int(_parse_timestr(entry.get("follow_up_at")) or 0)
        except Exception:
            normalized["follow_up_at"] = None

    return normalized


def _append_summary_to_history(user_id, new_summary, category, existing_history, follow_up_at=None):
    if not new_summary:
        return _normalize_summary_history(existing_history)

    history = _normalize_summary_history(existing_history)


    if any(
        isinstance(item, dict) and item.get("important_info") == (new_summary.get("important_info") if isinstance(new_summary, dict) else new_summary)
        for item in history
    ):
        return history

    created_at = int(time.time())
    expires_at = _calculate_expiration(category)

    parsed_follow_up = None
    if follow_up_at is not None:
        parsed_follow_up = _safe_int(_parse_timestr(follow_up_at), None)
    elif isinstance(new_summary, dict) and new_summary.get("follow_up_at") is not None:
        parsed_follow_up = _safe_int(_parse_timestr(new_summary.get("follow_up_at")), None)

    new_entry = {
        "important_info": (new_summary.get("important_info") if isinstance(new_summary, dict) else new_summary) or "",
        "category": category,
        "created_at": created_at,
        "expires_at": expires_at,
    }

    if parsed_follow_up is not None:
        new_entry["follow_up_at"] = parsed_follow_up
    history.append(new_entry)

    try:
        if user_id:
            save_firebase_user(user_id, {"summary_history": history})
    except Exception as exc:
        print(f"Failed to persist summary history for {user_id}: {exc}")

    return history


def _summary_is_expired(entry, now=None):
    if not entry or entry.get("expires_at") is None:
        return False

    current = int(now if now is not None else time.time())
    return int(entry["expires_at"]) <= current


def _build_summary_notification(item):
    return build_notification_for_item(item)


def get_pending_summary_notifications(user_id, now=None):
    if not user_id:
        return []

    user = load_firebase_user(user_id)
    active = _normalize_summary_history(user.get("summary_history", []) or [])
    current = int(now if now is not None else time.time())

    pending = []
    for item in active:
        if item.get("status") == "active" and _summary_is_expired(item, current):
            try:
                notification = _build_summary_notification(item)
                pending.append({**item, "notification_ready": True, **notification})
            except Exception as exc:
                print(f"Failed to build notification for item {item.get('id')}: {exc}")
                pending.append({**item, "notification_ready": True, "notification_title": "هناك إشعار جديد", "notification_body": "راجع حالتك الطبية.", "notification_type": "confirmation"})

    return pending


def get_user_summary_lists(user_id, now=None):
    user = load_firebase_user(user_id) if user_id else {}
    active = _normalize_summary_history(user.get("summary_history", []) or [])
    finished = _normalize_summary_history(user.get("summary_finished", []) or [])
    archive = _normalize_summary_history(user.get("summary_archive", []) or [])
    pending = get_pending_summary_notifications(user_id, now=now)

    return {
        "active_summaries": active,
        "finished_summaries": finished,
        "archive_summaries": archive,
        "pending_notifications": pending,
    }


def extend_summary_item(user_id, item_id, additional_days=None):
    if not user_id:
        return None

    user = load_firebase_user(user_id)
    active = _normalize_summary_history(user.get("summary_history", []) or [])
    updated = []
    now = int(time.time())
    extended = None

    for item in active:
        if item["id"] == item_id:
            if additional_days is None:
                additional_days = EXPIRATION_DAYS.get(item.get("category"))
                if additional_days is None:
                    additional_days = 30
            item["expires_at"] = now + int(additional_days * 24 * 60 * 60)
            item["notification_ready"] = False
            item["extended_at"] = now
            item["extension_days"] = additional_days
            extended = item
        updated.append(item)

    if extended:
        save_firebase_user(user_id, {"summary_history": updated})

    return extended


def finalize_summary_item(user_id, item_id, ended_at=None, label=None):
    if not user_id:
        return None

    user = load_firebase_user(user_id)
    active = _normalize_summary_history(user.get("summary_history", []) or [])
    finished = _normalize_summary_history(user.get("summary_finished", []) or [])
    archive = _normalize_summary_history(user.get("summary_archive", []) or [])
    ended_at = int(ended_at or time.time())

    remaining = []
    finalized_item = None

    for item in active:
        if item["id"] == item_id:
            finalized_item = item
        else:
            remaining.append(item)

    if not finalized_item:
        return None

    retention_seconds = ended_at - finalized_item.get("created_at", ended_at)
    finalized_item = {
        **finalized_item,
        "status": "finished",
        "ended_at": ended_at,
        "retention_seconds": retention_seconds,
    }

    finished.append(finalized_item)
    archive_item = {
        "id": finalized_item["id"],
        "summary": finalized_item.get("summary") or finalized_item.get("important_info"),
        "important_info": finalized_item.get("important_info"),
        "label": label or finalized_item.get("summary") or finalized_item.get("important_info"),
        "category": finalized_item.get("category"),
        "started_at": finalized_item.get("created_at"),
        "ended_at": ended_at,
        "retention_seconds": retention_seconds,
        "source_status": "finished",
    }

    # preserve follow-up timestamp if present
    if finalized_item.get("follow_up_at") is not None:
        archive_item["follow_up_at"] = finalized_item.get("follow_up_at")

    archive.append(archive_item)
    save_firebase_user(user_id, {
        "summary_history": remaining,
        "summary_finished": finished,
        "summary_archive": archive,
    })

    return {
        "finished_item": finalized_item,
        "archive_item": archive_item,
    }


def _parse_timestr(val):
    from datetime import datetime
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except:
            try:
                return datetime.fromisoformat(val).timestamp()
            except:
                return 0
    return 0


def normalize_history(history):
    """Return history ordered from oldest -> newest when possible.
    Tries to sort by common timestamp/id keys. If it finds a monotonic
    numeric/id field that decreases (newest-first), it will reverse.
    Otherwise returns the history as-is.
    """
    if not history or not isinstance(history, list):
        return []

    # common keys that may indicate ordering
    keys = ['timestamp', 'time', 'created_at', 'date', 'ts', 'created', 'id', 'index', 'idx']

    for key in keys:
        if all(isinstance(h, dict) and (key in h) and (h.get(key) is not None) for h in history):
            # try numeric sort
            vals = [h.get(key) for h in history]
            # if numeric-like
            if all(isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()) for v in vals):
                nums = [float(v) for v in vals]
                # if decreasing, reverse to make oldest->newest
                if nums[0] > nums[-1]:
                    return list(reversed(history))
                else:
                    return history

            # try parseable time strings
            parsed = [_parse_timestr(v) for v in vals]
            if any(parsed):
                if parsed[0] > parsed[-1]:
                    return list(reversed(history))
                else:
                    return history

    # fallback: if first message text equals latest user text pattern it's likely newest-first
    return history


def summarize_messages(snippet_msgs, max_len=120):
    """Create a short one-line snippet per message for quick context."""
    summaries = []
    for m in snippet_msgs:
        sender = m.get('sender', 'user')
        text = m.get('text', '') or ''
        text = ' '.join(text.split())
        if len(text) > max_len:
            text = text[:max_len].rstrip() + '...'
        label = 'User' if sender == 'user' else 'Assistant'
        summaries.append(f"{label}: {text}")
    return summaries


def format_chat_for_display(chat_history, max_messages=6):
    """Return a plain-text friendly summary and snippets for display (not JSON-heavy).
    Returns a dict: {formatted_history, message_summaries, conversation_summary}
    """
    norm = normalize_history(chat_history or [])
    recent = norm[-max_messages:] if norm else []

    # build readable conversation block
    block = []
    for m in recent:
        sender = 'User' if m.get('sender') == 'user' else 'Assistant'
        text = (m.get('text') or '').strip().replace('\n', ' ')
        block.append(f"{sender}: {text}")

    message_summaries = summarize_messages(recent)

    # simple conversation summary heuristic
    user_texts = [m.get('text','') for m in recent if m.get('sender') == 'user']
    conv_summary = ''
    if user_texts:
        first = user_texts[0].strip().replace('\n',' ')[:140]
        last = user_texts[-1].strip().replace('\n',' ')[:140]
        if first and last and first != last:
            conv_summary = f"From earlier: {first} ... Most recently: {last}"
        else:
            conv_summary = first or last

    return {
        'formatted_history': '\n'.join(block),
        'message_summaries': message_summaries,
        'conversation_summary': conv_summary
    }

def analyze_user_semantics(text, max_retries=3, default_risk=0):
    full_prompt = USER_ANALYSING_PROMPT_1 + "\n\nUser message:\n" + (text or "")

    for attempt in range(max_retries):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": "qwen2:1.5b-instruct",
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
            ai_reply = data.get("response", "")

            parsed = _safe_json_loads(ai_reply, {})
            risk = parsed.get("risk", default_risk) if isinstance(parsed, dict) else default_risk

            if isinstance(risk, str) and risk.isdigit():
                risk = int(risk)

            if risk in [0, 1, 2, 3]:
                return risk
            print(f"Attempt {attempt+1}: Invalid risk '{risk}', retrying...")
        except requests.RequestException as e:
            print(f"Attempt {attempt+1}: Request error: {e}")
        except Exception as e:
            print(f"Attempt {attempt+1}: Unexpected error: {e}")

    print(f"No valid risk obtained after {max_retries} attempts. Using default risk {default_risk}.")
    return default_risk
    
def analyze_user_samantics2(text, max_retries=3, default_type=0):

    full_prompt = USER_ANALYSING_PROMPT_2 + "\n\nUser message:\n" + (text or "")

    for attempt in range(max_retries):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": "qwen2:1.5b-instruct",
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
            ai_reply = data.get("response", "")

            parsed = _safe_json_loads(ai_reply, {})
            msg_type = parsed.get("type", default_type) if isinstance(parsed, dict) else default_type

            if isinstance(msg_type, str) and msg_type.isdigit():
                msg_type = int(msg_type)

            if msg_type in range(8):
                return msg_type
            print(f"Attempt {attempt+1}: Invalid type '{msg_type}', retrying...")
        except requests.RequestException as e:
            print(f"Attempt {attempt+1}: Request error: {e}")
        except Exception as e:
            print(f"Attempt {attempt+1}: Unexpected error: {e}")

    print(f"No valid type obtained after {max_retries} attempts. Using default type {default_type}.")
    return default_type

def analyze_ai_response(text, answer):

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
              },
              timeout=20
       )
       response.raise_for_status()
       try:
           return response.json()
       except ValueError:
           print("AI answer response was not valid JSON")
           return None
   except requests.RequestException as e:
         print("Error:", e)
         return None
   except Exception as e:
         print("Unexpected error in analyze_ai_response:", e)
         return None
   
def classify_ai_response(text):

   full_prompt = PROMPT_AI_CLASSIFICATION + "\n\nAI response:\n" + (text or "")

   try:
       response = requests.post(
              OLLAMA_URL,
              json={
                "model": "qwen2:1.5b-instruct",
                "prompt": full_prompt,
                "stream": False
              },
              timeout=20
       )
       response.raise_for_status()

       data = response.json()
       raw = data.get("response", "")

       parsed = _safe_json_loads(raw, {})
       if isinstance(parsed, dict):
           return parsed.get("class")
       return None

   except Exception as e:
         print("Error:", e)
         return None

def ai_system(text, user_classification, doctor_type, chat_history, user_data, image_base64=None, language=None):
    reason = user_classification.get("reason") if isinstance(user_classification, dict) else None
    doctor_profile = get_doctor_profile(doctor_type)

    print("DOCTOR PROFILE:", doctor_profile)

    print("LANGUAGE:", language)

    user_info = json.dumps(user_data, indent=2, ensure_ascii=False)

    formatted_history = ""

    try:
        print("RAW HISTORY:")
        for i, msg in enumerate(chat_history or []):
            if isinstance(msg, dict):
                print(i, msg.get("sender"), repr(msg.get("text", "")[:50]))
            else:
                print(i, repr(str(msg)[:50]))
    except Exception as exc:
        print(f"Failed to print raw history: {exc}")

    # normalize ordering to oldest -> newest when possible
    norm_history = normalize_history(chat_history or [])

    # remove any duplicate of the current user message (client may include it)
    norm_history = [m for m in norm_history if not (m.get('sender') == 'user' and m.get('text', '').strip() == text.strip())]

    # take the most recent 6 messages (chronological order)
    recent = norm_history[-6:] if norm_history else []

    # build formatted conversation (oldest -> newest)
    for msg in recent:
        sender = msg.get("sender")
        content = msg.get("text", "")

        if sender == "user":
            formatted_history += f"User: {content}\n"

        elif sender == "ai":
            formatted_history += f"Assistant: {content}\n"

    # add lightweight summaries to improve context without dumping full JSON
    message_summaries = summarize_messages(recent)
    conversation_summary = ''
    if message_summaries:
        # simple heuristic summary: first + last user snippets
        user_texts = [m.get('text','') for m in recent if m.get('sender') == 'user']
        if user_texts:
            first = user_texts[0].strip().replace('\n',' ')[:140]
            last = user_texts[-1].strip().replace('\n',' ')[:140]
            if first and last and first != last:
                conversation_summary = f"From earlier: {first} ... Most recently: {last}"
            else:
                conversation_summary = first or last

    # append summaries to the formatted_history so the model gets concise context
    if conversation_summary:
        formatted_history = f"CONVERSATION SUMMARY: {conversation_summary}\n\nRECENT MESSAGES:\n{formatted_history}\nMESSAGE_SUMMARIES:\n" + "\n".join(message_summaries)

    print("FORMATTED HISTORY:\n", repr(formatted_history))

    image_analysis = None
    if image_base64:
        try:
            image_analysis = analyze_image(image_base64)
            print("IMAGE ANALYSIS:", repr(image_analysis))
        except Exception as exc:
            print(f"Image analysis failed: {exc}")
            image_analysis = None

    reply = None
    try:
        if reason == "Emergency":
            reply = generate_emergency_response(text, language, image_analysis=image_analysis)
        elif reason == "Self-harm":
            reply = generate_self_harm_response(text, language, image_analysis=image_analysis)
        else:
            reply = generate_standard_response(
                text,
                doctor_profile,
                user_info,
                language=language,
                image_analysis=image_analysis,
                chat_history=formatted_history
            )
    except Exception as exc:
        print(f"AI response generation failed: {exc}")
        reply = None

    print("RAW REPLY:", repr(reply))

    if not reply or not isinstance(reply, str) or reply.strip() == "":
        try:
            reply = generate_standard_response(
                text,
                doctor_profile,
                user_info,
                language=language,
                chat_history=formatted_history,
                image_analysis=image_analysis
            )
        except Exception as exc:
            print(f"Fallback response generation failed: {exc}")
            reply = "عذرًا، حدث خطأ داخلي أثناء تجهيز الرد."

    print("LANGUAGE CHECK FAILED")

    return reply

def ai_for_illegal_cases(text, ai_reply, ai_classification,user_data):
    commander = ai_classification.get("status", "SAFE")

    if commander == "UNSAFE":
        refined_reply = refine_response(text, ai_reply, user_data)
        return refined_reply
    
    elif commander == "SAFE":
        return ai_reply
    
def Performance_evaluation_ai(user_message, ai_reply):
    full_prompt = _build_evaluation_prompt(user_message, ai_reply)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen2:1.5b-instruct",
                "prompt": full_prompt,
                "stream": False
            },
            timeout=20
        )

        response.raise_for_status()

        try:
            result = response.json()
            evaluation_text = result.get("response", "").strip()
            return evaluation_text
        except ValueError:
            print("Performance evaluation response was not valid JSON")
            return None

    except requests.RequestException as e:
        print("Error:", e)
        return None
    except Exception as e:
        print("Unexpected error in Performance_evaluation_ai:", e)
        return None
   
def title_creation(text, language=None):
    fallback = "New Conversation"

    if len(text.strip()) < 10:
        return fallback

    title = title_creator(text, language)

    if not title:
        return fallback

    title = (
        title
        .replace('"', '')
        .replace("Title:", "")
        .strip()
    )

    if title == "":
        return fallback

    return title


def _clean_text_value(text):
    if not isinstance(text, str):
        return text

    cleaned = text.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in ('"', "'"):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def analyze_image(image_base64, mock=False):
    if not image_base64:
        return None

    if mock:
        print("Mock image analysis enabled.")
        return "Mock image analysis: image data received and ready for processing."

    try:
        print("BASE64 LENGTH:", len(image_base64))

        analysis = Image_captioner(image_base64)

        print("IMAGE ANALYSIS RESULT:", repr(analysis))

        analysis = _clean_text_value(analysis)
        if not analysis:
            return None

        return analysis

    except Exception as exc:
        print("Image analysis failed:", exc)
        return None

 

def user_info_history(text, user_id=None):

    classification = _safe_json_loads(classify_user_message(text), {})
    if not isinstance(classification, dict):
        classification = {}
    if classification.get("class") != 1:
        return None

    resume = _safe_json_loads(resume_message(text), {})
    if not isinstance(resume, dict) or "important_info" not in resume:
        return None
    

    if not isinstance(resume, dict) or "important_info" not in resume:
        return None

    firebase_user = load_firebase_user(user_id) if user_id else {}
    medical_info = firebase_user.get("medical", {}) or {}
    existing_history = firebase_user.get("summary_history", []) or []

    print("EXISTING HISTORY:", repr(existing_history))
    print("USER MEDICAL INFO:", repr(medical_info))
    print("RESUME:", repr(resume))

    user_medical_text = _format_medical_info(medical_info)
    previous_summary_text = _format_summary_history(existing_history)

    print("USER MEDICAL TEXT:", repr(user_medical_text))
    print("PREVIOUS SUMMARY TEXT:", repr(previous_summary_text))

    # duplicate = None
    # try:
    raw_duplicate = None
    duplicate = {"duplicate": 1}
    try:
        raw_duplicate = detect_duplicate(
            resume["important_info"],
            user_medical_text,
            previous_summary_text,
        )
        duplicate = _safe_json_loads(raw_duplicate, {"duplicate": 1}) or {"duplicate": 1}
    except Exception as exc:
        print(f"Failed to detect duplicate: {exc}")
        duplicate = {"duplicate": 1}

    category = {"category": None}
    try:
        category = _safe_json_loads(classify_resume(resume["important_info"]), {"category": None}) or {"category": None}
    except Exception as exc:
        print(f"Failed to classify resume: {exc}")
        category = {"category": None}

    if duplicate and duplicate.get("duplicate") == 0:
        updated_history = _append_summary_to_history(user_id, resume["important_info"], category.get("category"), existing_history)
    else:
        updated_history = _normalize_summary_history(existing_history)

    print ("UPDATED HISTORY:", repr(updated_history))
    return {
        "important_info": resume["important_info"],
        "category": category.get("category"),
        "duplicate": duplicate.get("duplicate") if isinstance(duplicate, dict) else None,
        "medical_info": medical_info,
        "summary_history": updated_history,
    }


def capture_user_medical_summary(user_id, text, user_data=None):
    """Capture medical summary information from the latest user message.

    This is designed to run after the AI reply so it does not block normal chat flow.
    The data is saved in Firebase and can later be consumed by React Native screens
    through notification/status endpoints.
    """
    if not user_id or not text or not isinstance(text, str):
        return None

    try:
        summary_payload = user_info_history(text, user_id)
    except Exception as exc:
        print("capture_user_medical_summary error:", exc)
        return None

    if not summary_payload:
        return None

    pending = get_pending_summary_notifications(user_id)
    return {
        "summary_capture": summary_payload,
        "pending_notifications": pending,
    }
    
