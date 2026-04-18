
doctors = ["general" , "pediatrician", "cardiologist", "dermatologist", "psychiatrist", "neurologist"]

def select_doctor():
    print("Available doctor:")
    for i,doctor in enumerate(doctors,1):
        print(f" {i}. {doctor}" )
        
    while True:
        choice = input("Enter the nember of the doctor you want:")
        if choice.isdigit() and 1 <= int(choice) <= len(doctors): #هنا عملنا على الحصر  بحيث حصرنا القيم بين 1 وطول القائمة
            return doctors[int(choice)-1]
        else:
            print("Invalid choice. Please try again.")
