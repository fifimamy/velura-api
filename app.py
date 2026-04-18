from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

FILE = "users.json"

# تحميل البيانات
def load_data():
    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            return json.load(f)
    return {}

# حفظ البيانات
def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


# ✅ حفظ المستخدم
@app.route("/save_user", methods=["POST"])
def save_user():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    users = load_data()
    users[user_id] = data
    save_data(users)

    return jsonify({"status": "saved"})


# ✅ جلب المستخدم
@app.route("/get_user", methods=["GET"])
def get_user():
    user_id = request.args.get("user_id")

    users = load_data()
    return jsonify(users.get(user_id, {}))


# ✅ حفظ المحادثات
@app.route("/save_chats", methods=["POST"])
def save_chats():
    data = request.json
    user_id = data.get("user_id")
    chats = data.get("chats")

    users = load_data()

    if user_id not in users:
        users[user_id] = {}

    users[user_id]["chats"] = chats

    save_data(users)

    return jsonify({"status": "chats saved"})


# ✅ جلب المحادثات
@app.route("/get_chats", methods=["GET"])
def get_chats():
    user_id = request.args.get("user_id")

    users = load_data()

    return jsonify(users.get(user_id, {}).get("chats", []))

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message")

    # 🔥 هنا الذكاء الاصطناعي (مؤقت)
    reply = f"تم استلام رسالتك: {message}"

    return jsonify({"reply": reply})

@app.route("/")
def home():
    return "Server running"

@app.route("/debug")
def debug():
    users = load_data()
    return jsonify(users)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)