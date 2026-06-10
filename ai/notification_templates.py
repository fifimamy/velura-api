from datetime import datetime

DEFAULT_NOTIFICATION = {
    "notification_title": "تحقق من الحالة الطبية",
    "notification_body": "هناك حالة طبية جاهزة للمراجعة.",
    "notification_type": "confirmation",
}

CONDITION_TEMPLATES = [
    {
        "keywords": ["كسر", "كسور", "fracture", "broken"],
        "title": "هل التام الكسر؟",
        "body": "الكسر التالي قد انتهت مدته: {summary}. هل تم الشفاء؟",
    },
    {
        "keywords": ["زكام", "نزلة برد", "برد", "سعال", "انفلونزا", "حمى", "cold", "flu"],
        "title": "هل انتهى الزكام؟",
        "body": "الحالة التالية قد انتهت مدتها: {summary}. هل انتهى المرض؟",
    },
    {
        "keywords": ["حساسية", "تحسس", "حساسية غذائية", "أعراض تحسس", "allergy"],
        "title": "هل لا تزال الحساسية موجودة؟",
        "body": "الحساسية التالية قد انتهت مدتها: {summary}. هل يجب إبقاؤها أم إنهاؤها؟",
    },
    {
        "keywords": ["دواء", "علاج", "مضاد حيوي", "أقراص", "حقنة", "medication", "treatment", "therapy"],
        "title": "هل انتهى العلاج؟",
        "body": "العلاج التالي قد انتهت مدته: {summary}. هل انتهى أو يحتاج تمديد؟",
    },
    {
        "keywords": ["جراحة", "عملية", "surgery", "operation"],
        "title": "هل انتهى التعافي بعد العملية؟",
        "body": "المتابعة بعد العملية: {summary}. هل تعافيت أم تحتاج متابعة إضافية؟",
    },
    {
        "keywords": ["مريض", "مستشفى", "حالة حرجة", "Hamid", "admitted", "hospital"],
        "title": "هل تحسنت الحالة بعد الاستشفاء؟",
        "body": "راجع حالة المريض: {summary}. هل هناك تحسن أو متابعة مطلوبة؟",
    },
    {
        "keywords": ["ضغط", "ضغط الدم", "hypertension", "blood pressure"],
        "title": "هل استقر ضغط الدم؟",
        "body": "الحالة التالية قد تحتاج متابعة: {summary}. هل ضغط الدم تحت السيطرة؟",
    },
    {
        "keywords": ["سكر", "سكري", "diabetes", "blood sugar"],
        "title": "هل تم ضبط سكر الدم؟",
        "body": "راجع الحالة التالية: {summary}. هل يحتاج المريض تعديل علاج السكر؟",
    },
    {
        "keywords": ["ربو", "asma", "asthma", "shortness of breath", "wheezing"],
        "title": "هل استقر الربو؟",
        "body": "الحالة التالية قد تحتاج متابعة: {summary}. هل الأعراض تحت السيطرة؟",
    },
    {
        "keywords": ["صداع", "Migraine", "صداع نصفي", "headache"],
        "title": "هل انتهى الصداع؟",
        "body": "الحالة التالية متعلقة بالصداع: {summary}. هل خفت الأعراض؟",
    },
    {
        "keywords": ["معدة", "ألم معدة", "غثيان", "قيء", "stomach", "nausea", "vomit"],
        "title": "هل تحسنت حالة المعدة؟",
        "body": "راجع الحالة التالية: {summary}. هل زال ألم المعدة أو الغثيان؟",
    },
    {
        "keywords": ["جرح", "إصابة", "cut", "wound", "injury", "scar"],
        "title": "هل التئم الجرح؟",
        "body": "المتابعة بعد الإصابة: {summary}. هل الجرح نظيف ويشفى بشكل جيد؟",
    },
    {
        "keywords": ["حاجة متابعة", "متابعة", "follow up", "follow-up", "appointment"],
        "title": "هل حان موعد المتابعة؟",
        "body": "هناك متابعة مطلوبة للحالة: {summary}. هل حان الوقت لإعادة التقييم؟",
    },
    {
        "keywords": ["ملف", "test", "نتيجة", "فحص", "analysis", "lab"],
        "title": "هل تأكدت من نتائج الفحص؟",
        "body": "الرجاء مراجعة نتائج الفحص المتعلقة بـ: {summary}. هل تحتاج إجراء أو متابعة؟",
    },
]

CATEGORY_TEMPLATES = {
    "chronic": {
        "title": "هل ما زالت الحالة المزمنة مستمرة؟",
        "body": "فضلاً راجع: {summary}. اضغط لتأكيد الاستمرار أو وقف الحالة.",
    },
    "allergy": {
        "title": "هل لا تزال هذه الحساسية سارية؟",
        "body": "الحساسية: {summary}. اضغط لتأكيد استمرارها أو إنهائها.",
    },
}


def _format_follow_up_date(timestamp):
    if not timestamp:
        return None
    try:
        timestamp = int(timestamp)
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
    except Exception:
        return None


def build_notification_for_item(item):
    if not item:
        return DEFAULT_NOTIFICATION.copy()

    summary_text = (item.get("summary") or item.get("important_info") or "هذه الحالة").strip()
    lower_summary = summary_text.lower()
    follow_up_date = _format_follow_up_date(item.get("follow_up_at"))

    for template in CONDITION_TEMPLATES:
        if any(keyword in lower_summary for keyword in template["keywords"]):
            title = template["title"]
            body = template["body"].format(summary=summary_text)
            if follow_up_date:
                body = f"{body} (متابعة مجدولة في {follow_up_date})"
            return {
                "notification_title": title,
                "notification_body": body,
                "notification_type": "confirmation",
            }

    category = item.get("category")
    if category in CATEGORY_TEMPLATES:
        template = CATEGORY_TEMPLATES[category]
        body = template["body"].format(summary=summary_text)
        if follow_up_date:
            body = f"{body} (متابعة مجدولة في {follow_up_date})"
        return {
            "notification_title": template["title"],
            "notification_body": body,
            "notification_type": "confirmation",
        }

    notification_title = "هل انتهت هذه الحالة؟"
    notification_body = f"الحالة: {summary_text}. اضغط لتأكيد انتهاءها أو تمديدها."
    if follow_up_date:
        notification_body = f"{notification_body} (متابعة مجدولة في {follow_up_date})"

    return {
        "notification_title": notification_title,
        "notification_body": notification_body,
        "notification_type": "confirmation",
    }
