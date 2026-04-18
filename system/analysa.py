from system.simple_analysis import analyze_text
from system.user_masseg import user_masseg





def Manual_user_filter (answer):
 text = analyze_text(answer)
 if text == "anxiety":
    return "normal"
 elif text == "sadness":
    return "normal"
 elif text == "fatigue":
    return "normal"
 elif text == "suicide":
   return "danger"
 elif text == "drugs":
   return "danger"
 elif text == "diagnosis":
    return "forbidden"
 else:
    return "unknown"
 

def Manual_ai_filter (ai_reply):
   text = analyze_text(ai_reply)

   if text == "Diagnosis_response":
       return "Diagnosis_response"
   elif text == "pharmaceutical":
       return "pharmaceutical"
   elif text == "Ethics":
       return "Ethics"
   elif text == "Passion":
       return "Passion"
   elif text == "The role":
       return "The role"
   elif text == "damage":
       return "damage"
   elif text == "System":
       return "system"
   else:
        return "SAFE"