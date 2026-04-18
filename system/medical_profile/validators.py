from system.medical_profile.fields import CHRONIC_DISEASES, ALLERGIES, LIMITS, GENDER_OPTIONS

def select_the_chronic_diseases():
    print("Select chronic diseases you have (comma separated numbers):")
    for i, disease in enumerate(CHRONIC_DISEASES, 1):
        print(f" {i}. {disease}")

    choices = input("Your choices: ")

    selected_diseases = []
    for choice in choices.split(","):
        choice = choice.strip()
        if choice.isdigit() and 1 <= int(choice) <= len(CHRONIC_DISEASES):
            disease = CHRONIC_DISEASES[int(choice) - 1]
            if disease not in selected_diseases:
                selected_diseases.append(disease)
    return selected_diseases

def select_allergies():
    print("Select allergies you have (comma separated numbers):")
    for i, allergy in enumerate(ALLERGIES, 1):
        print(f" {i}. {allergy}")

    choices = input("Your choices: ")

    selected_allergies = []
    for choice in choices.split(","):
        choice = choice.strip()
        if choice.isdigit() and 1 <= int(choice) <= len(ALLERGIES):
            allergy = ALLERGIES[int(choice) - 1]
            if allergy not in selected_allergies:
                selected_allergies.append(allergy)

    return selected_allergies
    

def select_gender():
    print("Select your gender:")
    for i, gender in enumerate(GENDER_OPTIONS, 1):
        print(f" {i}. {gender}")

    choice = input("Your choice: ")
    if choice.isdigit() and 1 <= int(choice) <= len(GENDER_OPTIONS):
        return GENDER_OPTIONS[int(choice) - 1]
    else:
        print("Invalid choice. Please try again.")
        return select_gender()

def validate_numeric_input(prompt, field_name):
    min_value, max_value = LIMITS[field_name]
    while True:
        value = input(prompt)
        if value.isdigit() and min_value <= int(value) <= max_value:
            return int(value)
        else:
            print(f"Invalid input. Please enter a number between {min_value} and {max_value}.")
def validate_age():
    return validate_numeric_input("Age: ", "age")
def validate_height():
    return validate_numeric_input("Height (cm): ", "height_cm")
def validate_weight():
    return validate_numeric_input("Weight (kg): ", "weight_kg")
 
  
