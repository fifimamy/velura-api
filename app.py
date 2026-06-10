from datetime import datetime
from flask import Flask, request, jsonify
import json
import os
import base64
from system.chat_engine import process_chat
from ai.semantic_analyzer import (
    format_chat_for_display,
    get_user_summary_lists,
    get_pending_summary_notifications,
    extend_summary_item,
    finalize_summary_item,
)
from system.firebase import load_user, load_all_users, update_user


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for a in args:
            if isinstance(a, str):
                safe_args.append(a.encode('ascii', errors='backslashreplace').decode('ascii'))
            else:
                safe_args.append(a)
        print(*safe_args, **kwargs)


app = Flask(__name__)

FIREBASE_DB_URL = os.environ.get("FIREBASE_DB_URL", "").rstrip("/")


# ✅ حفظ المستخدم
@app.route("/save_user", methods=["POST"])
def save_user():
    if not FIREBASE_DB_URL:
        return jsonify({"status": "error", "error": "FIREBASE_DB_URL is not configured"}), 503

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "error": "user_id is required"}), 400

    if "medical" in data:
        update_user(user_id, {"medical": data["medical"]})
    else:
        update_user(user_id, {})

    return jsonify({"status": "saved"})

@app.route("/get_user", methods=["GET"])
def get_user():
    user_id = request.args.get("user_id")
    return jsonify(load_user(user_id))

@app.route("/summary_status", methods=["GET"])
def summary_status():
    user_id = request.args.get("user_id")
    return jsonify(get_user_summary_lists(user_id))


@app.route("/summary_notifications", methods=["GET"])
def summary_notifications():
    user_id = request.args.get("user_id")
    return jsonify(get_pending_summary_notifications(user_id))


@app.route("/summary_extend", methods=["POST"])
def summary_extend():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    item_id = data.get("item_id")
    additional_days = data.get("additional_days")

    if additional_days is not None:
        try:
            additional_days = float(additional_days)
        except (TypeError, ValueError):
            additional_days = None

    updated = extend_summary_item(user_id, item_id, additional_days)
    if not updated:
        return jsonify({"status": "error", "error": "item not found or user_id missing"}), 404

    return jsonify({"status": "extended", "item": updated})


@app.route("/summary_finish", methods=["POST"])
def summary_finish():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    item_id = data.get("item_id")
    ended_at = data.get("ended_at")
    label = data.get("label")

    if ended_at is not None:
        try:
            ended_at = int(ended_at)
        except (TypeError, ValueError):
            ended_at = None

    result = finalize_summary_item(user_id, item_id, ended_at=ended_at, label=label)
    if not result:
        return jsonify({"status": "error", "error": "item not found or user_id missing"}), 404

    return jsonify({"status": "finalized", "finished": result["finished_item"], "archive": result["archive_item"]})


# ✅ حفظ المحادثات
@app.route("/save_chats", methods=["POST"])
def save_chats():
    if not FIREBASE_DB_URL:
        return jsonify({"status": "error", "error": "FIREBASE_DB_URL is not configured"}), 503

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    chats = data.get("chats")

    if not user_id:
        return jsonify({"status": "error", "error": "user_id is required"}), 400

    update_user(user_id, {"chats": chats})

    return jsonify({"status": "chats saved"})


# ✅ جلب المحادثات
@app.route("/get_chats", methods=["GET"])
def get_chats():
    user_id = request.args.get("user_id")
    user_data = load_user(user_id)
    return jsonify(user_data.get("chats", []))


@app.route("/get_chats_display", methods=["GET"])
def get_chats_display():
    """Return a human-friendly plain-text summary of the user's chats.
    Useful for UI that prefers concise text instead of raw JSON.
    """
    user_id = request.args.get("user_id")
    chats = load_user(user_id).get("chats", [])

    if not chats:
        return ("No conversations found.", 200, {"Content-Type": "text/plain; charset=utf-8"})

    summary = format_chat_for_display(chats, max_messages=8)

    parts = []
    if summary.get('conversation_summary'):
        parts.append("Conversation summary:")
        parts.append(summary['conversation_summary'])
        parts.append("")

    parts.append("Recent messages:")
    parts.append(summary['formatted_history'])
    parts.append("")
    parts.append("Message snippets:")
    parts.extend(summary['message_summaries'])

    text = "\n".join(parts)

    return (text, 200, {"Content-Type": "text/plain; charset=utf-8"})

@app.route("/chat", methods=["POST"])
def chat():

    try:

        message = request.form.get("message")
        doctor_type = request.form.get("doctor_type", "general")
        user_id = request.form.get("user_id")

        # history
        chat_history = request.form.get("chat_history")

        safe_print("\n--- NEW REQUEST ---")
        safe_print("MESSAGE:", repr(message))
        safe_print("DOCTOR:", repr(doctor_type))
        safe_print("USER:", repr(user_id))
        safe_print("HAS HISTORY:", bool(chat_history))
        safe_print("-------------------\n")

        if chat_history:
           try:
              chat_history = json.loads(chat_history)
           except:
              chat_history = []
        else:
            chat_history = []

        # image
        image = request.files.get("image")
        if image and image.content_length:
         if image.content_length > 10 * 1024 * 1024:
          return jsonify({
            "success": False,
            "error": "Image too large"
            }), 400

        image_base64 = None

        if image:
            image_bytes = image.read()

            image_base64 = base64.b64encode(
                image_bytes
            ).decode("utf-8")

        # validation
        if not message and not image:
            return jsonify({
                "success": False,
                "error": "No message or image provided"
            }), 400

        # load user data
        user_data = load_user(user_id)

        # language should come from the saved Firebase user profile
        language = user_data.get("language") or user_data.get("lang")

        # process ai
        result = process_chat(
            message=message,
            doctor_type=doctor_type,
            user_data=user_data,
            user_id=user_id,
            chat_history=chat_history,
            image_base64=image_base64,
            language=language
        )

        return jsonify({
            "success": True,
            "response": result,
            "time": datetime.utcnow().isoformat()
        })

    except Exception as e:

        print("CHAT ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    



@app.route("/")
def home():
    return "Server running"

@app.route("/debug")
def debug():
    return jsonify(load_all_users())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)



