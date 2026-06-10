from system.doctor_selector import select_doctor
from system.doctor_responses import get_doctor_response
from system.medical_profile.user_information import collect_user_information
from system.user_masseg import user_masseg, ai_masseg
from system.user_filter import final_classification
from ai.ai_filter import final_classification_ai
from ai.semantic_analyzer import ai_system 
from system.storage import append_chat_exchange, store_user_data, stor_ai_evaluation
from ai.semantic_analyzer import ai_for_illegal_cases
from ai.ai_filter import evaluation
import json

with open("user_data.json","r",encoding= "utf-8") as f:
 user_data = json.load(f)

# with open("conversation.json", "r", encoding="utf-8") as f:
#  history = json.load(f)

# collect_user_information()

doctor_type = select_doctor()

get_doctor_response(doctor_type)

chat_history = []

while True:
    answer = user_masseg().strip()

    if answer.lower() in ["exit", "quit", "bye"]:
        print("Thank you for chatting. Take care!")
        break
  
    user_result = final_classification(answer)  #تصنيف رسالة المستخدم 

    print("=== User Classification ===")
    print(user_result)
    
    ai_reply = ai_system(answer, user_result,doctor_type, chat_history, user_data)    #رد الذكاء الاصطناعي

    append_chat_exchange(answer, ai_reply)

    print("=== AI Reply ===")
    print(ai_reply)

    # ai_classification = final_classification_ai(answer, ai_reply)  #تصنيف رد الذكاء الاصطناعي

    # print("=== AI Classification ===")
    # print(ai_classification)

    # reply = ai_for_illegal_cases(answer,ai_reply,ai_classification, user_data) #اعادة توليد رد الذكاء الاصطناعي في حالات الاختراق
    
    # store_ai_input(reply)    #حفظ رد الذكاء الاصطناعي
    
    # print("=== Final Reply ===")
    # print(reply)
    
    # evalu = evaluation(answer,reply) #تقييم الذكاء لإصطناعي
    # stor_ai_evaluation(evalu) 






