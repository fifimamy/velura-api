import os
import json
import requests
from urllib.parse import quote

FIREBASE_DB_URL = os.environ.get("FIREBASE_DB_URL", "").rstrip("/")
FIREBASE_AUTH_TOKEN = os.environ.get("FIREBASE_AUTH_TOKEN")


def firebase_url(path: str) -> str:
    if not FIREBASE_DB_URL:
        raise RuntimeError("FIREBASE_DB_URL is not configured")

    firebase_path = path.strip("/")
    url = f"{FIREBASE_DB_URL}/{firebase_path}.json"

    if FIREBASE_AUTH_TOKEN:
        url = f"{url}?auth={quote(FIREBASE_AUTH_TOKEN, safe='')}"

    return url


def firebase_request(path: str, method: str = "GET", payload=None):
    url = firebase_url(path)
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=15)
        elif method.upper() == "PATCH":
            response = requests.patch(url, json=payload, timeout=15)
        elif method.upper() == "PUT":
            response = requests.put(url, json=payload, timeout=15)
        elif method.upper() == "POST":
            response = requests.post(url, json=payload, timeout=15)
        else:
            response = requests.request(method.upper(), url, json=payload, timeout=15)

        response.raise_for_status()
        if not response.content:
            return None

        try:
            return response.json()
        except ValueError:
            return None
    except requests.RequestException as exc:
        print(f"Firebase request failed: {exc}")
        return None
    except Exception as exc:
        print(f"Unexpected Firebase error: {exc}")
        return None


def load_user(user_id):
    if not user_id or not FIREBASE_DB_URL:
        return {}

    result = firebase_request(f"users/{user_id}", method="GET")
    return result or {}


def load_all_users():
    if not FIREBASE_DB_URL:
        return {}

    result = firebase_request("users", method="GET")
    return result or {}


def update_user(user_id, payload):
    if not user_id:
        raise ValueError("user_id is required")
    if not FIREBASE_DB_URL:
        raise RuntimeError("Firebase is not configured")

    return firebase_request(f"users/{user_id}", method="PATCH", payload=payload)


def push_user_item(user_id, collection, payload):
    if not user_id:
        raise ValueError("user_id is required")
    return firebase_request(f"users/{user_id}/{collection}", method="POST", payload=payload)


def save_ai_evaluation_to_firebase(user_id, evaluation_data):
    return push_user_item(user_id, "ai_evaluations", evaluation_data)


def load_firebase_user(user_id):
    return load_user(user_id)


def save_firebase_user(user_id, payload):
    return update_user(user_id, payload)
