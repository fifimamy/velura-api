import json
import os
import time


def _read_json_file(filename, default=None):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        return default

    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, ValueError):
        return default
    except Exception:
        return default


def _write_json_file(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_conversation(filename="conversation.json"):
    data = _read_json_file(filename, default=[])
    if not isinstance(data, list):
        return []
    return data


def append_chat_exchange(user_message, ai_reply, filename="conversation.json"):
    if user_message is None and ai_reply is None:
        return None

    history = load_conversation(filename)
    entry = {
        "user": user_message or "",
        "ai": ai_reply or "",
        "timestamp": int(time.time())
    }
    history.append(entry)
    _write_json_file(filename, history)
    return entry


def store_user_input(text, filename="conversation.json"):
    history = load_conversation(filename)
    history.append({"user": text, "ai": "", "timestamp": int(time.time())})
    _write_json_file(filename, history)
    return history[-1]


def store_ai_input(text, filename="conversation.json"):
    history = load_conversation(filename)
    if history and isinstance(history[-1], dict) and history[-1].get("ai", "") == "":
        history[-1]["ai"] = text
        history[-1]["timestamp"] = int(time.time())
    else:
        history.append({"user": "", "ai": text, "timestamp": int(time.time())})
    _write_json_file(filename, history)
    return history[-1]


def store_user_data(data, filename="user_data.json"):
    _write_json_file(filename, data)
    return data


def store_ai_evaluation(data, filename="evaluation.json"):
    existing_data = _read_json_file(filename, default=[])
    if not isinstance(existing_data, list):
        existing_data = []

    existing_data.append(data)
    _write_json_file(filename, existing_data)
    return data


stor_ai_evaluation = store_ai_evaluation
