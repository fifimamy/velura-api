from system.medical_profile.validators import  validate_numeric_input, select_the_chronic_diseases, select_allergies,select_gender
from system.storage import store_user_data

def collect_user_information():
    user_data = {}

    user_data['name'] = input("Enter your full name: ")
    user_data['age'] = validate_numeric_input("Enter your age: ", "age")
    user_data['gender'] = select_gender()
    user_data['height_cm'] = validate_numeric_input("Enter your height (cm): ", "height_cm")
    user_data['weight_kg'] = validate_numeric_input("Enter your weight (kg): ", "weight_kg")
    user_data['chronic_diseases'] = select_the_chronic_diseases()
    user_data['allergies'] = select_allergies()
    user_data['other_user_notes'] = input("Enter any other relevant health information or notes: ")
    

    store_user_data(user_data)
    
    return user_data
