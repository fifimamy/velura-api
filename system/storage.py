import os
import json

def store_user_input(text):
    
    filename = "conversation.json"
    data = []

    # إذا كان الملف موجود ويحتوي بيانات، اقرأ القائمة القديمة
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = []

    # أضف الرسالة الجديدة
    data.append({"user": text})

    # اكتب القائمة كاملة من جديد
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def store_ai_input(text):
    filename = "conversation.json"
    data = []

    # إذا كان الملف موجود ويحتوي بيانات، اقرأ القائمة القديمة
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = []

    # أضف رسالة الذكاء الاصطناعي الجديدة
    data.append({"ai": text})

    # اكتب القائمة كاملة من جديد
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def store_user_data(data):
    with open("user_data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def stor_ai_evaluation(data):

    filename = "evaluation.json"

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_data.append(data)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(existing_data, file, indent=4, ensure_ascii=False)
