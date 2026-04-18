from system.conversation_data import user_data

def get_doctor_response(doctor_name):
    user_data["doctor"] = doctor_name

    if doctor_name == "general":
        print("I am your general doctor")
        print("I can help with a wide range of health issues.")
        
    elif doctor_name == "pediatrician":
        print("I am your pediatrician")
        print("I specialize in children's health.")
        
    elif doctor_name == "cardiologist":
        print("I am your cardiologist")
        print("I focus on heart health and related issues.")
           
    elif doctor_name == "dermatologist":
        print("I am your dermatologist")
        print("I specialize in skin health and conditions.")

    elif doctor_name == "psychiatrist":
        print("I am your psychiatrist")
        print("I can help with mental health concerns and emotional well-being.")
    
    elif doctor_name == "neurologist":
        print("I am your neurologist")
        print("I specialize in disorders of the nervous system, including the brain and spinal cord.")

    else:
        print("Unknown doctor type.")


  
    return 


        


       

    