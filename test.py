from system.user_masseg import user_masseg
from ai.semantic_analyzer import user_info_history
import json

user_id = {
  "name": "fifi",
  "age": 15,
  "gender": "Female",
  "height_cm": 165,
  "weight_kg": 59,
  "chronic_diseases": [],
  "allergies": [],
  "other_user_notes": ""
}
while True:
 user_message = user_masseg()

 if user_message.lower() == "bey" :
   break
 
 user_info = user_info_history(user_message, user_id)

 print ("USER INFO HISTORY:", json.dumps(user_info, indent=2))