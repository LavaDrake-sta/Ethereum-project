import pandas as pd
from werkzeug.security import generate_password_hash

# פונקציה ליצירת קובץ Excel לרופאים
def create_doctors_excel():
    columns = ['Name', 'ID', 'Specialty', 'Username', 'Password']
    df = pd.DataFrame(columns=columns)
    df.to_excel('doctors.xlsx', index=False)
    print("doctors.xlsx created successfully.")

# פונקציה ליצירת קובץ Excel למטופלים
def create_patients_excel():
    columns = ['Name', 'ID', 'Age', 'Address', 'Phone', 'HMO']
    df = pd.DataFrame(columns=columns)
    df.to_excel('patients.xlsx', index=False)
    print("patients.xlsx created successfully.")

# פונקציה ליצירת קובץ Excel לתרופות
def create_medications_excel():
    columns = ['Name', 'Dosage', 'Description', 'Stock']
    df = pd.DataFrame(columns=columns)
    df.to_excel('medications.xlsx', index=False)
    print("medications.xlsx created successfully.")

# פונקציה להוספת רופא ל-Excel
def add_doctor_to_excel(name, doctor_id, specialty, username, password):
    password_hash = generate_password_hash(password)
    
    if not pd.read_excel('doctors.xlsx').empty:
        df = pd.read_excel('doctors.xlsx')
    else:
        df = pd.DataFrame(columns=['Name', 'ID', 'Specialty', 'Username', 'Password'])
    
    new_doctor = pd.DataFrame([{
        'Name': name,
        'ID': doctor_id,
        'Specialty': specialty,
        'Username': username,
        'Password': password_hash
    }])
    
    df = pd.concat([df, new_doctor], ignore_index=True)
    df.to_excel('doctors.xlsx', index=False)
    print(f"Doctor {name} added successfully.")

# פונקציה להוספת מטופל ל-Excel
def add_patient_to_excel(name, patient_id, age, address, phone, hmo):
    if not pd.read_excel('patients.xlsx').empty:
        df = pd.read_excel('patients.xlsx')
    else:
        df = pd.DataFrame(columns=['Name', 'ID', 'Age', 'Address', 'Phone', 'HMO'])
    
    new_patient = pd.DataFrame([{
        'Name': name,
        'ID': patient_id,
        'Age': age,
        'Address': address,
        'Phone': phone,
        'HMO': hmo
    }])
    
    df = pd.concat([df, new_patient], ignore_index=True)
    df.to_excel('patients.xlsx', index=False)
    print(f"Patient {name} added successfully.")

# פונקציה להוספת תרופה ל-Excel
def add_medication_to_excel(name, dosage, description, stock):
    if not pd.read_excel('medications.xlsx').empty:
        df = pd.read_excel('medications.xlsx')
    else:
        df = pd.DataFrame(columns=['Name', 'Dosage', 'Description', 'Stock'])
    
    new_medication = pd.DataFrame([{
        'Name': name,
        'Dosage': dosage,
        'Description': description,
        'Stock': stock
    }])
    
    df = pd.concat([df, new_medication], ignore_index=True)
    df.to_excel('medications.xlsx', index=False)
    print(f"Medication {name} added successfully.")

if __name__ == "__main__":
    create_doctors_excel()
    create_patients_excel()
    create_medications_excel()

    