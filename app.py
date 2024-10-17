from flask import Flask, render_template, request, redirect, url_for, flash
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from web3 import Web3
import webbrowser

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# הגדרת Flask-Login לניהול תהליכי כניסה ויציאה של משתמשים
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# פרטי התחברות קבועים למנהל
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = generate_password_hash('admin123')

# ABI וכתובת החוזה החכם מה-Remix
abi = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [
            { "internalType": "address", "name": "doctorAddress", "type": "address" },
            { "internalType": "string", "name": "_doctorId", "type": "string" },
            { "internalType": "string", "name": "_username", "type": "string" },
            { "internalType": "string", "name": "_password", "type": "string" },
            { "internalType": "string", "name": "_specialty", "type": "string" }
        ],
        "name": "addDoctor",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            { "internalType": "address", "name": "doctorAddress", "type": "address" }
        ],
        "name": "removeDoctor",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            { "internalType": "string", "name": "_patientId", "type": "string" },
            { "internalType": "string", "name": "_name", "type": "string" },
            { "internalType": "uint256", "name": "_age", "type": "uint256" },
            { "internalType": "string", "name": "_addressPatient", "type": "string" },
            { "internalType": "string", "name": "_hmo", "type": "string" }
        ],
        "name": "addPatient",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            { "internalType": "string", "name": "_patientId", "type": "string" },
            { "internalType": "string", "name": "_doctorId", "type": "string" },
            { "internalType": "string", "name": "_treatmentDetails", "type": "string" }
        ],
        "name": "addRecord",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{ "internalType": "string", "name": "_patientId", "type": "string" }],
        "name": "getRecords",
        "outputs": [
            {
                "components": [
                    { "internalType": "string", "name": "patientId", "type": "string" },
                    { "internalType": "string", "name": "doctorId", "type": "string" },
                    { "internalType": "string", "name": "treatmentDetails", "type": "string" },
                    { "internalType": "uint256", "name": "timestamp", "type": "uint256" }
                ],
                "internalType": "struct MedicalRecords.Record[]",
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{ "internalType": "address", "name": "doctorAddress", "type": "address" }],
        "name": "getDoctor",
        "outputs": [
            { "internalType": "string", "name": "", "type": "string" },
            { "internalType": "string", "name": "", "type": "string" },
            { "internalType": "bool", "name": "", "type": "bool" }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            { "internalType": "string", "name": "_username", "type": "string" },
            { "internalType": "string", "name": "_password", "type": "string" }
        ],
        "name": "authenticateDoctor",
        "outputs": [{ "internalType": "bool", "name": "", "type": "bool" }],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getMedications",
        "outputs": [
            {
                "components": [
                    { "internalType": "string", "name": "name", "type": "string" },
                    { "internalType": "uint256", "name": "dosage", "type": "uint256" },
                    { "internalType": "uint256", "name": "stock", "type": "uint256" }
                ],
                "internalType": "struct MedicalRecords.Medication[]",
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

contract_address = '0x97798a47094371c8B200fcdA59dB2F3E61f11098'

# פונקציה לחיבור לבלוקצ'יין בהתאם לספק הנבחר
def connect_blockchain(provider_type='ganache'):
    try:
        if provider_type == 'ganache':
            w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
            if w3.is_connected():
                print("Connected to Ganache")
                flash('Connected to Ganache successfully.', 'success')
            else:
                raise ConnectionError("Connection to Ganache failed")
        elif provider_type == 'metamask':
            w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
            if w3.is_connected():
                print("Connected to MetaMask")
                flash('Connected to MetaMask successfully.', 'success')
            else:
                raise ConnectionError("Connection to MetaMask failed")
        else:
            raise ValueError("Invalid provider type")
        return w3
    except Exception as e:
        flash(f"Failed to connect to blockchain: {e}", 'danger')
        return None
    
def sign_transaction(w3, tx):
    account = w3.eth.accounts[0]  # Ganache
    private_key = 'PRIVATE_KEY_HERE'  # הכנס את המפתח הפרטי שלך

    try:
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction sent: {tx_hash.hex()}")
        flash('Transaction signed and sent successfully.', 'success')
        return tx_hash
    except Exception as e:
        flash(f"Failed to sign or send transaction: {e}", 'danger')
        return None
    
# מחלקת User לניהול משתמשים ב-LoginManager
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(username):
    if username == ADMIN_USERNAME:
        return User(username)
    return None

# פונקציה להוספת רשומה רפואית לבלוקצ'יין
def add_treatment_record(patient_id, name, doctor_id, treatment_details, provider_type='ganache'):
    try:
        w3 = connect_blockchain(provider_type)
        contract = w3.eth.contract(address=contract_address, abi=abi)

        tx_hash = contract.functions.addRecord(
            patient_id, name, doctor_id, treatment_details
        ).transact({
            'from': w3.eth.accounts[0],
            'gas': 200000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash('Treatment record added to blockchain.', 'success')
    except Exception as e:
        flash(f'Failed to add treatment record: {e}', 'danger')

def check_balance(w3):
    balance = w3.eth.get_balance(w3.eth.accounts[0])
    balance_in_eth = w3.fromWei(balance, 'ether')
    return balance_in_eth

# פונקציה להוספת תרופה לבלוקצ'יין
def add_medication(name, dosage, stock, provider_type='ganache'):
    try:
        w3 = connect_blockchain(provider_type)
        contract = w3.eth.contract(address=contract_address, abi=abi)

        tx_hash = contract.functions.addMedication(
            name, dosage, stock
        ).transact({
            'from': w3.eth.accounts[0],
            'gas': 200000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash('Medication added to blockchain.', 'success')
    except Exception as e:
        flash(f'Failed to add medication: {e}', 'danger')

def is_valid_id(patient_id):
    return patient_id.isdigit() and len(patient_id) == 9

def is_valid_phone(phone):
    return phone.isdigit() and len(phone) == 10

def add_doctor_to_blockchain(doctor_address, doctor_id, username, password, specialty, provider_type='ganache'):
    try:
        # חיבור לבלוקצ'יין
        w3 = connect_blockchain(provider_type)
        contract = w3.eth.contract(address=contract_address, abi=abi)

        # וידוא כתובת חוקית
        if not Web3.is_address(doctor_address):
            raise ValueError("Invalid doctor address format")

        # חשבון ממנו תתבצע העסקה
        account = w3.eth.accounts[0]

        # הכנת הטרנזקציה
        tx = contract.functions.addDoctor(
            Web3.to_checksum_address(doctor_address),  # כתובת בפורמט נכון
            doctor_id, username, password, specialty
        ).build_transaction({
            'from': account,
            'gas': 200000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account),
        })

        # חתימת הטרנזקציה עם המפתח הפרטי
        private_key = '0xYOUR_PRIVATE_KEY'  # הכנס מפתח פרטי מתאים
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)

        # שליחת הטרנזקציה
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print("Doctor added successfully:", tx_receipt.transactionHash.hex())
        flash('Doctor added successfully!', 'success')

    except ValueError as ve:
        flash(f"Address Error: {ve}", 'danger')
        print(f"Address Error: {ve}")

    except Exception as e:
        print(f"Error adding doctor: {e}")
        flash(f"Error adding doctor: {e}", 'danger')

def authenticate_doctor(username, password, provider_type='ganache'):
    try:
        w3 = connect_blockchain(provider_type)
        contract = w3.eth.contract(address=contract_address, abi=abi)

        # יצירת האש של הסיסמה שהוזנה
        password_hash = w3.keccak(text=password)

        # שליפת פרטי הרופא מהחוזה לפי שם משתמש
        doctor = contract.functions.doctors(username).call()

        if doctor[2] == password_hash.hex():  # השוואת ההאש של הסיסמה
            return True  # אימות הצליח
        else:
            return False  # אימות נכשל
    except Exception as e:
        flash(f'Authentication failed: {e}', 'danger')
        return False

def add_treatment_record(patient_id, name, doctor_id, treatment_details, provider_type='ganache'):
    try:
        w3 = connect_blockchain(provider_type)
        contract = w3.eth.contract(address=contract_address, abi=abi)

        # בדיקת יתרה לפני שליחת עסקה
        balance_in_eth = check_balance(w3)
        if balance_in_eth <= 0:
            flash('אין לך מספיק יתרה בחשבון', 'danger')
            return

        tx_hash = contract.functions.addRecord(
            patient_id, name, doctor_id, treatment_details
        ).transact({
            'from': w3.eth.accounts[0],
            'gas': 200000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash('רשומת מטופל הוספה לבלוקצ\'יין', 'success')
    except Exception as e:
        flash(f'שגיאה בהוספת רשומת מטופל: {e}', 'danger')

@app.route('/get_patient/<patient_id>')
def get_patient(patient_id):
    try:
        w3 = connect_blockchain()
        contract = w3.eth.contract(address=contract_address, abi=abi)
        patient_records = contract.functions.getRecords(patient_id).call()

        return render_template('patient_details.html', records=patient_records)
    except Exception as e:
        flash(f'Failed to get patient details: {e}', 'danger')
        return redirect(url_for('admin_dashboard'))
    
@app.route('/edit_medication/<int:id>', methods=['POST'])
@login_required
def edit_medication(medication_id, new_stock):
    try:
        w3 = connect_blockchain('ganache')
        contract = w3.eth.contract(address=contract_address, abi=abi)
        tx_hash = contract.functions.updateMedicationStock(medication_id, new_stock).transact({
            'from': w3.eth.accounts[0],
            'gas': 200000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash('Medication stock updated successfully.', 'success')
    except Exception as e:
        flash(f'Failed to update medication stock: {e}', 'danger')

@app.route('/connect_provider', methods=['POST'])
def connect_provider():
    provider_type = request.form.get('provider_type')
    w3 = connect_blockchain(provider_type)
    if w3:
        flash(f'Connected to {provider_type} successfully!', 'success')
    else:
        flash(f'Failed to connect to {provider_type}.', 'danger')
    return redirect(url_for('admin_dashboard'))

# פונקציית התחברות
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # בדיקת התחברות כאדמין
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD, password):
            user = User(username)
            login_user(user)
            return redirect(url_for('admin_dashboard'))

        # בדיקת התחברות כרופא
        elif authenticate_doctor(username, password):
            user = User(username)
            login_user(user)
            return redirect(url_for('doctor_dashboard'))

        flash('Login failed. Invalid username or password.', 'danger')

    return render_template('login.html')

# פונקציה ללוח הבקרה של האדמין
@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.id != ADMIN_USERNAME:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # לוגיקה להוספת תרופה
        if 'add_medication' in request.form:
            name = request.form['medication_name']
            dosage = request.form['dosage']
            stock = request.form['stock']
            # קריאה לפונקציה להוספת תרופה
            add_medication(name, int(dosage), int(stock), provider_type=request.form.get('provider_type', 'ganache'))

        # לוגיקה לעריכת מלאי תרופות
        elif 'edit_medication' in request.form:
            medication_id = request.form['medication_id']
            new_stock = request.form['new_stock']
            # קריאה לפונקציה לעריכת המלאי של תרופה
            edit_medication(int(medication_id), int(new_stock))

    # שליפת רופאים, מטופלים ותרופות להצגה בלוח הבקרה
    doctors = get_all_doctors()
    patients = get_all_patients()
    medications = get_all_medications()

    return render_template('admin_dashboard.html', doctors=doctors, patients=patients, medications=medications)

@app.route('/add_doctor', methods=['POST'])
@login_required
def add_doctor_route():
    doctor_address = request.form['doctor_address']
    doctor_id = request.form['doctor_id']
    username = request.form['username']
    password = request.form['password']
    specialty = request.form['specialty']

    if not doctor_address.startswith('0x') or len(doctor_address) != 42:
        flash('Invalid doctor address.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        add_doctor_to_blockchain(doctor_address, doctor_id, username, password, specialty)
        flash('Doctor added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding doctor: {e}', 'danger')

    return redirect(url_for('admin_dashboard'))

# פונקציות לשליפת כל הרופאים, המטופלים והתרופות
def get_all_doctors():
    try:
        w3 = connect_blockchain()
        contract = w3.eth.contract(address=contract_address, abi=abi)
        doctor_list = contract.functions.getDoctors().call()
        return doctor_list
    except Exception as e:
        flash(f'Failed to get doctors: {e}', 'danger')
        return []

def get_all_medications():
    try:
        w3 = connect_blockchain()
        contract = w3.eth.contract(address=contract_address, abi=abi)
        medications = contract.functions.getMedications().call()
        return medications
    except Exception as e:
        flash(f'Failed to get medications: {e}', 'danger')
        return []
    
def get_all_patients():
    try:
        # חיבור לבלוקצ'יין
        w3 = connect_blockchain('ganache')  # או 'metamask' בהתאם לצורך שלך
        contract = w3.eth.contract(address=contract_address, abi=abi)

        # שליפה של רשימת המטופלים (בהתאם לפונקציות בחוזה החכם שלך)
        patient_list = []  # הכנס כאן לוגיקה לשליפת המטופלים
        for patient_id in contract.functions.getPatientIds().call():
            patient_data = contract.functions.getPatient(patient_id).call()
            patient = {
                'ID': patient_id,
                'Name': patient_data[0],
                'Age': patient_data[1],
                'Address': patient_data[2],
                'HMO': patient_data[3]
            }
            patient_list.append(patient)

        return patient_list

    except Exception as e:
        flash(f'Failed to get patients: {e}', 'danger')
        return []


# עמוד רופא
@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    return render_template('doctor_dashboard.html')

# יציאה מהמערכת
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# פונקציה לפתיחת הדפדפן
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    from threading import Timer
    Timer(1, open_browser).start()
    app.run(debug=True)