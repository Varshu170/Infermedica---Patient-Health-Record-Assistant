from flask import Flask, jsonify, request, make_response, render_template, send_from_directory
from pymongo import MongoClient
import pdfkit
import json
from pympler import asizeof
import ast
import torch
from transformers import BartForConditionalGeneration, BartTokenizer, PegasusForConditionalGeneration, PegasusTokenizer
import speech_recognition as sr
from gtts import gTTS
import pygame
import os

# Load models and tokenizers
model_bart = BartForConditionalGeneration.from_pretrained('finetuned-bart-latest')
tokenizer_bart = BartTokenizer.from_pretrained('finetuned-bart-latest')
model_pegasus = PegasusForConditionalGeneration.from_pretrained('pegasus_intents_model_new')
tokenizer_pegasus = PegasusTokenizer.from_pretrained('pegasus_intents_tokenizer_new')


# Specify the path to the wkhtmltopdf executable
path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
css_path = 'static/style.css'

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['mydb']
collection = db['patients']


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/patients-section')
def patients_section():
    return render_template('index-pat.html')

@app.route('/doctors-section')
def doctors_section():
    return render_template('index-doc.html')

@app.route('/insurance-section')
def insurance_section():
    return render_template('index-ins.html')


def generate_description_by_claim_id(data_list):
    descriptions = []
    for data in data_list:
        description = "<html><body>"
        description += f"<h2>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Patient ID: {data['id']}</h2>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Name:</strong> {data['name']['first']} {data['name']['last']}</p>"

        insurance = data['insurance']
        if 'claimed_insurance' in insurance and len(insurance['claimed_insurance']) > 0:
            description += "<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Claimed Insurance:</strong></p>"
            for claim in insurance['claimed_insurance']:
                description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Claim ID:</strong> {claim['claim_id']}</p>"
                description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Date:</strong> {claim['date']}</p>"
                description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Amount:</strong> {claim['amount']}</p>"
                description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Status:</strong> {claim['status']}</p>"

        description += "</body></html>"
        descriptions.append(description)

    return "\n\n".join(descriptions)


def generate_description_by_insurance_name(data_list):
    descriptions = []
    for data in data_list:
        description = "<html><body>"
        description += f"<h2>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Patient ID: {data.get('id', 'NA')}</h2>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Name:</strong> {data.get('name', {}).get('first', 'NA')} {data.get('name', {}).get('last', 'NA')}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Age:</strong> {data.get('age', 'NA')}</p>"

        insurance = data.get('insurance', {})
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Insurance Provider:</strong> {insurance.get('provider', 'NA')}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Policy Number:</strong> {insurance.get('policy_number', 'NA')}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Group Number:</strong> {insurance.get('group_number', 'NA')}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Policy Effective Date:</strong> {insurance.get('effective_date', 'NA')}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Policy Expiration Date:</strong> {insurance.get('expiration_date', 'NA')}</p>"

        # Handle missing 'nominee' field
        nominee = insurance.get('nominee')
        if nominee:
            nominee_name = nominee.get('name', 'NA')
            nominee_relationship = nominee.get('relationship', 'NA')
            nominee_contact = nominee.get('contact', 'NA')
        else:
            nominee_name = 'NA'
            nominee_relationship = 'NA'
            nominee_contact = 'NA'
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Nominee:</strong> {nominee_name} ({nominee_relationship}) - {nominee_contact}</p>"

        claimed_insurance = insurance.get('claimed_insurance', [])
        if claimed_insurance:
            description += "<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Claimed Insurance:</strong></p>"
            for claim in claimed_insurance:
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  - Claim ID: {claim.get('claim_id', 'NA')}, Date: {claim.get('date', 'NA')}, Amount: {claim.get('amount', 'NA')}, Status: {claim.get('status', 'NA')}</p>"

        description += "</body></html>"
        descriptions.append(description)

    return "\n\n".join(descriptions)



def generate_description_patients(data_list):
    descriptions = []

    for data in data_list:
        description = "<html><body>"

        # Basic Information
        description += f"<h2>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Patient ID: {data['id']}</h2>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Name:</strong> {data['name']['first']} {data['name']['last']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Age:</strong> {data['age']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Date of Birth:</strong> {data['dob']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Gender:</strong> {data['gender']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Blood Group:</strong> {data['blood_group']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Weight:</strong> {data['weight']}</p>"

        # Contact Information
        contact = data['contact']
        address = contact['address']
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Contact Phone:</strong> {contact['phone']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Address:</strong> {address['street']}, {address['city']}, {address['state']} {address['zip']}, {address['country']}</p>"

        # Emergency Contact
        emergency_contact = data['emergency_contact']
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Emergency Contact:</strong> {emergency_contact['name']} ({emergency_contact['relationship']}) - {emergency_contact['phone']}</p>"

        # Insurance Information
        insurance = data['insurance']
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Insurance Provider:</strong> {insurance['provider']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Policy Number:</strong> {insurance['policy_number']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Group Number:</strong> {insurance['group_number']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Policy Effective Date:</strong> {insurance['effective_date']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Policy Expiration Date:</strong> {insurance['expiration_date']}</p>"
        nominee = insurance['nominee']
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Nominee:</strong> {nominee['name']} ({nominee['relationship']}) - {nominee['contact']}</p>"

        # Claimed Insurance
        description += "<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Claimed Insurance:</strong></p>"
        for claim in insurance['claimed_insurance']:
            description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Claim ID: {claim['claim_id']}, Date: {claim['date']}, Amount: {claim['amount']}, Status: {claim['status']}</p>"

        # Medical History
        medical_history = data['medical_history']
        description += "<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Medical History:</strong></p>"
        if 'allergies' in medical_history:
            description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Allergies: {', '.join(medical_history['allergies'])}</p>"
        if 'conditions' in medical_history and len(medical_history['conditions']) > 0:
            description += "<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Conditions:</p>"
            for condition in medical_history['conditions']:
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    - {condition['name']} (Diagnosed on: {condition['diagnosed_date']}, Status: {condition['status']})</p>"
        if 'surgeries' in medical_history and len(medical_history['surgeries']) > 0:
            description += "<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Surgeries:</p>"
            for surgery in medical_history['surgeries']:
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;      - {surgery['name']} (Date: {surgery['date']}, Outcome: {surgery['outcome']})</p>"
        if 'medications' in medical_history and len(medical_history['medications']) > 0:
            description += "<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Medications:</p>"
            for medication in medical_history['medications']:
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  - {medication['name']} (Dose: {medication['dose']}, Frequency: {medication['frequency']}, Start Date: {medication['start_date']})</p>"

        # Appointments
        if 'appointments' in data and len(data['appointments']) > 0:
            description += "<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Appointments:</strong></p>"
            for appointment in data['appointments']:
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; - Date: {appointment['date']}, Type: {appointment['type']}</p>"
                doctor = appointment['doctor']
                doctor_address = doctor['contact']['address']
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    Doctor: {doctor['name']} (Specialty: {doctor['specialty']})</p>"
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Contact: {doctor['contact']['phone']}, Address: {doctor_address['street']}, {doctor_address['city']}, {doctor_address['state']} {doctor_address['zip']}, {doctor_address['country']}</p>"
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    Notes: {appointment['notes']}</p>"

                # Lab Tests
                if 'lab_tests' in appointment and len(appointment['lab_tests']) > 0:
                    description += "<p>&nbsp;&nbsp;&nbsp;&nbsp;    Lab Tests:</p>"
                    for test in appointment['lab_tests']:
                        results = test['results']
                        description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;      - Test: {test['test_name']} (Date: {test['date']})</p>"
                        description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       Findings: {results.get('findings', 'N/A')}, Conclusion: {results.get('conclusion', 'N/A')}</p>"

        # Test Results
        if 'test_results' in data and len(data['test_results']) > 0:
            description += "<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Test Results:</strong></p>"
            for test_result in data['test_results']:
                results = test_result['results']
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  - Test: {test_result['test_name']} (Date: {test_result['date']})</p>"
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;   Findings: {results['findings']}, Conclusion: {results['conclusion']}</p>"

        # Health Monitoring
        if 'health_monitoring' in data and 'daily_vitals' in data['health_monitoring']:
            description += "<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Daily Vitals:</strong></p>"
            for vitals in data['health_monitoring']['daily_vitals']:
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  - Date: {vitals['date']}, Blood Pressure: {vitals['blood_pressure']}, Heart Rate: {vitals['heart_rate']}, Temperature: {vitals['temperature']}°F</p>"

        description += "</body></html>"

        descriptions.append(description)
    print(descriptions)
    return "\n\n".join(descriptions)


def generate_description_doctor(data_list):
    descriptions = []

    for data in data_list:
        description = "<html><body>"

        # Basic Information
        description += f"<h2>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Patient ID: {data['id']}</h2>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Name:</strong> {data['name']['first']} {data['name']['last']}</p>"
        description += f"<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Date of Birth:</strong> {data['dob']}</p>"

        # Medical History
        medical_history = data['medical_history']
        description += "<p><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Medical History:</strong></p>"

        # Unique Allergies
        if 'allergies' in medical_history:
            unique_allergies = set(medical_history['allergies'])  # Use a set to remove duplicates
            description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Allergies: {', '.join(unique_allergies)}</p>"

        if 'conditions' in medical_history and len(medical_history['conditions']) > 0:
            description += "<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Conditions:</p>"
            for condition in medical_history['conditions']:
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    - {condition['name']} (Diagnosed on: {condition['diagnosed_date']}, Status: {condition['status']})</p>"

        if 'surgeries' in medical_history and len(medical_history['surgeries']) > 0:
            description += "<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Surgeries:</p>"
            for surgery in medical_history['surgeries']:
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    - {surgery['name']} (Date: {surgery['date']}, Outcome: {surgery['outcome']})</p>"

        if 'medications' in medical_history and len(medical_history['medications']) > 0:
            description += "<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Medications:</p>"
            for medication in medical_history['medications']:
                description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    - {medication['name']} (Dose: {medication['dose']}, Frequency: {medication['frequency']}, Start Date: {medication['start_date']})</p>"

        description += "</body></html>"

        descriptions.append(description)

    return "\n\n".join(descriptions)

def conditions_description(patients,con_name):
    descriptions = []
    for patient in patients:
        description = "<html><body>"
        name = f"{patient['name']['first']} {patient['name']['last']}"
        patient_id = patient['id']
        age = patient['age']

        description += f"<p>Name: {name}, ID: {patient_id}, Age: {age}</p>"

        medical_history = patient.get('medical_history', {})

        if 'conditions' in medical_history and len(medical_history['conditions']) > 0:
            description += "<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Conditions:</p>"
            for condition in medical_history['conditions']:
                if condition['name']==con_name:
                    description += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; - {condition['name']} (Diagnosed on: {condition['diagnosed_date']}, Status: {condition['status']})</p>"
        description += "</body></html>"
        descriptions.append(description)
    return "\n\n".join(descriptions)

def surgeries_description(patients,surgery_name):
    descriptions = []
    for patient in patients:
            description = "<html><body>"
            if 'surgeries' in patient['medical_history'] and len(patient['medical_history']['surgeries']) > 0:
                description += f"<p>Patient {patient['name']['first']} {patient['name']['last']} (ID: {patient['id']}):</p>"
                description += "<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Surgeries:</p>"
                for surgery in patient['medical_history']['surgeries']:
                    if surgery['name']==surgery_name:
                        description += (f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                    f"- {surgery['name']} (Date: {surgery['date']}, Outcome: {surgery['outcome']})</p>")
                description += "</body></html>"
            descriptions.append(description)
    return "\n\n".join(descriptions)

@app.route('/patients', methods=['POST'])
def patients():
    data = request.json
    query_type = data.get('query_type')
    patient_description = ""

    if query_type == 'single':
        patient_id = data.get('id')
        patient_data = collection.find_one({"id": patient_id})
        if patient_data:
            patient_description = generate_description_patients([patient_data])
        else:
            patient_description = "Patient not found."
    elif query_type == 'multiple':
        start_id = data.get('start_id')
        end_id = data.get('end_id')
        patient_data_list = list(collection.find({"id": {"$gte": start_id, "$lte": end_id}}))
        if patient_data_list:
            patient_description = generate_description_patients(patient_data_list)
        else:
            patient_description = "No patients found in the given range."
    else:
        patient_description = "Invalid query type."

    return jsonify({'description': patient_description})


# Doctor Routes
@app.route('/fetch_patient_by_surgery', methods=['GET','POST'])
def fetch_patient_by_surgery():
    data = request.get_json()
    surgery_name = data.get('surgery_name')
    patient_data_list = list(collection.find({"medical_history.surgeries.name": surgery_name},
                                             {"id": 1, "name": 1, "age": 1, "medical_history.surgeries": 1}))

    if patient_data_list:
        print(patient_data_list,surgery_name)
        patient_description=surgeries_description(patient_data_list,surgery_name)
        return jsonify({'description': patient_description})
    else:
        return jsonify({'description': "No patients found for the specified surgery."})


# Route to fetch patients by condition
@app.route('/fetch_patient_by_condition', methods=['POST'])
def fetch_patient_by_condition():
    data = request.get_json()
    condition_name = data.get('condition_name')
    patient_data_list = list(collection.find({"medical_history.conditions.name": condition_name},
                                             {"id": 1, "name": 1, "age": 1, "medical_history.conditions": 1}))

    if patient_data_list:
        patient_description = conditions_description(patient_data_list, condition_name)
        return jsonify({'description': patient_description})
    else:
        return jsonify({'description': "No patients found for the specified condition."})

@app.route('/fetch_patient_by_doctor', methods=['POST'])
def fetch_patient_by_doctor():
    data = request.get_json()
    doctor_name = data.get('doctor_name')
    patient_data_list = list(collection.find({"appointments.doctor.name": doctor_name},
                                             {"id": 1, "name": 1, "dob": 1, "medical_history": 1}))

    if patient_data_list:
        patient_description = generate_description_doctor(patient_data_list)
        return jsonify({'description': patient_description})
    else:
        return jsonify({'description': "No patients found for the specified condition."})


# Insurance Routes
@app.route('/insurance', methods=['GET', 'POST'])
def insurance():
    data = request.json
    search_by = data.get('search_by')
    input_value = data.get('insurance_name') if search_by == 'insurance_name' else data.get('claim_id')

    if search_by == 'insurance_name':
        result = list(collection.find({"insurance.provider": input_value}))
        if result:
            description = generate_description_by_insurance_name(result)
        else:
            description = "No valid records found or data format is incorrect."
    else:
        result = list(collection.find({"insurance.claimed_insurance.claim_id": input_value}))
        if result:
            description = generate_description_by_claim_id(result)
        else:
            description = "No valid records found or data format is incorrect."

    return jsonify({'description': description})


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    data = request.get_json()
    description = data.get('description', '')
    pdf = pdfkit.from_string(description, False, configuration=config, css=css_path)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=patient_data.pdf'
    return response

def generate_query(question):
    inputs = tokenizer_bart(question, return_tensors='pt', max_length=512, truncation=True, padding="max_length")
    outputs = model_bart.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
    query = tokenizer_bart.decode(outputs[0], skip_special_tokens=True)
    print(query)
    return query

import json

def execute_query(query_string, patient_id=None):
    try:
        if query_string.startswith("db.patients.aggregate"):
            query_start = query_string.find('[')
            query_end = query_string.rfind(']') + 1
            pipeline_str = query_string[query_start:query_end]

            try:
                pipeline = json.loads(pipeline_str)
            except json.JSONDecodeError as e:
                print(f"An error occurred while parsing the aggregation pipeline: {e}")
                return None

            if patient_id:
                pipeline.insert(0, {"$match": {"id": patient_id}})

            results = list(collection.aggregate(pipeline))

        elif query_string.startswith("db.patients.find"):
            query_start = query_string.find('(') + 1
            query_end = query_string.rfind(')')
            query_content = query_string[query_start:query_end].strip()

            if not query_content:
                filter_query = {}
                projection_query = None
            else:
                try:
                    # Attempt to parse the content as JSON directly
                    json_content = json.loads(f"[{query_content}]")
                    filter_query = json_content[0]
                    projection_query = json_content[1] if len(json_content) > 1 else None
                except json.JSONDecodeError as e:
                    print(f"An error occurred while parsing the find query: {e}")
                    return None

            if patient_id:
                filter_query['id'] = patient_id

            results = list(collection.find(filter_query, projection_query))

        elif query_string.startswith("db.patients.findOne"):
            query_start = query_string.find('(') + 1
            query_end = query_string.rfind(')')
            query_content = query_string[query_start:query_end].strip()

            if not query_content:
                filter_query = {}
                projection_query = None
            else:
                try:
                    json_content = json.loads(f"[{query_content}]")
                    filter_query = json_content[0]
                    projection_query = json_content[1] if len(json_content) > 1 else None
                except json.JSONDecodeError as e:
                    print(f"An error occurred while parsing the findOne query: {e}")
                    return None

            if patient_id:
                filter_query['id'] = patient_id

            results = collection.find_one(filter_query, projection_query)
            results = [results] if results else []

        elif query_string.startswith("db.patients.countDocuments"):
            query_start = query_string.find('(') + 1
            query_end = query_string.rfind(')')
            filter_str = query_string[query_start:query_end]

            try:
                filter_query = json.loads(filter_str)
            except json.JSONDecodeError as e:
                print(f"An error occurred while parsing the countDocuments query: {e}")
                return None

            if patient_id:
                filter_query['id'] = patient_id

            count = collection.count_documents(filter_query)
            results = [{'count': count}]

        else:
            print("Unsupported query type.")
            return None

        print(results)
        return results

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


    
def generate_description(data_list):
    descriptions = []
    
    for data in data_list:
        description = ""

        # Basic Information
        description += f"Patient ID: {data['id']}\n"
        description += f"Name: {data['name']['first']} {data['name']['last']}\n"
        description += f"Age: {data['age']}\n"
        description += f"Date of Birth: {data['dob']}\n"
        description += f"Gender: {data['gender']}\n"
        description += f"Blood Group: {data['blood_group']}\n"
        description += f"Weight: {data['weight']}\n"

        # Contact Information
        contact = data['contact']
        address = contact['address']
        description += f"Contact Phone: {contact['phone']}\n"
        description += f"Address: {address['street']}, {address['city']}, {address['state']} {address['zip']}, {address['country']}\n"

        # Emergency Contact
        emergency_contact = data['emergency_contact']
        description += f"Emergency Contact: {emergency_contact['name']} ({emergency_contact['relationship']}) - {emergency_contact['phone']}\n"

        # Insurance Information
        insurance = data['insurance']
        description += f"Insurance Provider: {insurance['provider']}\n"
        description += f"Policy Number: {insurance['policy_number']}\n"
        description += f"Group Number: {insurance['group_number']}\n"
        description += f"Policy Effective Date: {insurance['effective_date']}\n"
        description += f"Policy Expiration Date: {insurance['expiration_date']}\n"
        nominee = insurance['nominee']
        description += f"Nominee: {nominee['name']} ({nominee['relationship']}) - {nominee['contact']}\n"

        # Claimed Insurance
        if 'claimed_insurance' in insurance and len(insurance['claimed_insurance']) > 0:
            description += "Claimed Insurance:\n"
            for claim in insurance['claimed_insurance']:
                description += f"  - Claim ID: {claim['claim_id']}, Date: {claim['date']}, Amount: {claim['amount']}, Status: {claim['status']}\n"

        # Medical History
        medical_history = data['medical_history']
        description += "Medical History:\n"
        if 'allergies' in medical_history:
            description += f"  Allergies: {', '.join(medical_history['allergies'])}\n"
        if 'conditions' in medical_history and len(medical_history['conditions']) > 0:
            description += "  Conditions:\n"
            for condition in medical_history['conditions']:
                description += f"    - {condition['name']} (Diagnosed on: {condition['diagnosed_date']}, Status: {condition['status']})\n"
        if 'surgeries' in medical_history and len(medical_history['surgeries']) > 0:
            description += "  Surgeries:\n"
            for surgery in medical_history['surgeries']:
                description += f"    - {surgery['name']} (Date: {surgery['date']}, Outcome: {surgery['outcome']})\n"
        if 'medications' in medical_history and len(medical_history['medications']) > 0:
            description += "  Medications:\n"
            for medication in medical_history['medications']:
                description += f"    - {medication['name']} (Dose: {medication['dose']}, Frequency: {medication['frequency']}, Start Date: {medication['start_date']})\n"

        # Appointments
        if 'appointments' in data and len(data['appointments']) > 0:
            description += "Appointments:\n"
            for appointment in data['appointments']:
                description += f"  - Date: {appointment['date']}, Type: {appointment['type']}\n"
                doctor = appointment['doctor']
                doctor_address = doctor['contact']['address']
                description += f"    Doctor: {doctor['name']} (Specialty: {doctor['specialty']})\n"
                description += f"    Contact: {doctor['contact']['phone']}, Address: {doctor_address['street']}, {doctor_address['city']}, {doctor_address['state']} {doctor_address['zip']}, {doctor_address['country']}\n"
                description += f"    Notes: {appointment['notes']}\n"

                # Lab Tests
                if 'lab_tests' in appointment and len(appointment['lab_tests']) > 0:
                    description += "    Lab Tests:\n"
                    for test in appointment['lab_tests']:
                        results = test['results']
                        description += f"      - Test: {test['test_name']} (Date: {test['date']})\n"
                        description += f"        Findings: {results.get('findings', 'N/A')}, Conclusion: {results.get('conclusion', 'N/A')}\n"

        # Test Results
        if 'test_results' in data and len(data['test_results']) > 0:
            description += "Test Results:\n"
            for test_result in data['test_results']:
                results = test_result['results']
                description += f"  - Test: {test_result['test_name']} (Date: {test_result['date']})\n"
                description += f"    Findings: {results['findings']}, Conclusion: {results['conclusion']}\n"

        # Health Monitoring
        if 'health_monitoring' in data and 'daily_vitals' in data['health_monitoring']:
            description += "Daily Vitals:\n"
            for vitals in data['health_monitoring']['daily_vitals']:
                description += f"  - Date: {vitals['date']}, Blood Pressure: {vitals['blood_pressure']}, Heart Rate: {vitals['heart_rate']}, Temperature: {vitals['temperature']}°F\n"

        descriptions.append(description)
    
    return "\n\n".join(descriptions)


# Function to convert data into natural language using PEGASUS
def convert_to_natural_language(data):
    input_text = json.dumps(data)
    inputs = tokenizer_pegasus(input_text, return_tensors='pt', truncation=True, padding=True)
    summary_ids = model_pegasus.generate(inputs['input_ids'])
    output = tokenizer_pegasus.decode(summary_ids[0], skip_special_tokens=True)
    return output

# Function to handle default responses
def default_responses(question):
    question=question.lower()
    if question in ["hi","hii","hey", "hai"]:
        return "Hello! How can I help you?"
    elif question in ["hello","helloo"]:
        return "Hello! How can I assist you today?"
    elif question in ["good morning","good afternoon","good evening","good night"]:
        return "Hello! What can I help you with?"
    elif question in ["what can you do?"]:
        return "I can help you with various tasks such as answering questions, providing information, and assisting with your needs. What would you like to know or do?"
    elif question in ["tell me about yourself", "who are you","who are you?"]:
        return "I'm a Patient Health Record Assistant. I'll help you with information retrieval and assist you with any questions or tasks you have. Feel free to ask me anything!"
    elif question in ["can you help me?","i need assistance"]:
        return "Of course! What do you need assistance with?"
    elif question in ["what is your name?"]:
        return "I’m an AI assistant. How can I help you today?"
    elif question in ["thank you"]:
        return  "You’re welcome! If you need anything else, feel free to ask."
    elif question in ["goodbye","see you"]:
        return "Bye! Have a great day. If you need assistance in the future, feel free to reach out."
    elif question in ["how can you assist me?"]:
        return "I can provide information, answer questions, and help with various tasks. What do you need help with?"
    elif question in ["what are the next steps?"]:
        return "Let me know what you’re referring to, and I can guide you through the next steps."
    elif question in ["do you understand me?"]:
        return "Yes, I’m programmed to understand and respond to your questions. What would you like to know?"
    elif question in ["can you give me some advice?"]:
        return "I can offer guidance and information based on your needs. How can I help you?"
    elif question in ["can you remind me of something?"]:
        return "I can help with reminders if you provide me with the details. What do you need a reminder for?"
    elif question in ["what’s the status of my request?"]:
        return "I can check the status if you provide me with details of your request. What is your request about?"
    elif question in ["i need more information"]:
        return "I’m here to provide details. What specific information are you looking for?"
    elif question in ["see you later","thanks","bye","i’m done"]:
        return "Thank you for reaching out. Have a great day!"
    elif question in ["is age a valid identifier?"]:
        return "For identification purposes, we primarily use ID numbers. Age alone cannot replace an ID. Please provide your ID for accurate processing."
    elif question in ["is dob an acceptable identifier?"]:
        return " We need your ID for proper identification purposes. Please provide your ID number."
    elif question in ["are there alternative ways to identify myself?"]:
        return "We require an ID number for proper identification. Please provide your id"
    elif question in ["is email address acceptable instead of id?"]:
        return "For identification and security reasons, an ID number is necessary. Providing a name, email address, or phone number alone is not sufficient. Please provide your ID number."
    elif question in ["how do i view my medical history?"]:
        return "Please provide your ID to access your complete medical history and details on your conditions."
    elif question in ["can i query specific health conditions from my records?"]:
        return "Yes, please specify the health condition and provide your ID for accurate information."
    elif question in ["what identification is required to access my medical records?"]:
        return "For accessing your medical records, an ID number is required. Please provide your ID for accurate processing."
    elif question in ["is it possible to access records with just a phone number?"]:
        return "For security reasons, a phone number alone is not sufficient to access records. An ID number is required."
    
    return None



@app.route('/process_voice', methods=['POST'])
def process_voice():
    # Initialize recognizer class (for recognizing the speech)
    r = sr.Recognizer()
    
    # Reading the audio file as source
    audio_file = request.files['audio']
    
    try:
        with sr.AudioFile(audio_file) as source:
            audio_text = r.listen(source)
            # Recognize speech using Google Speech Recognition
            text = r.recognize_google(audio_text)
            return jsonify({'text': text})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Speech recognition failed.'})

AUDIO_DIR = "/static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def text_to_speech(text, filename):
    # Convert the text to speech
    speech = gTTS(text=text, lang='en', slow=False)

    # Save the speech to an MP3 file
    filepath = os.path.join(AUDIO_DIR, filename)
    speech.save(filepath)
    return filepath

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question')
    patient_id = data.get('patient_id', None)

    # Check for default responses
    default_response = default_responses(question)
    if default_response:
        audio_filepath = text_to_speech(default_response, "default_response.mp3")
        return jsonify({'response': default_response, 'audio_url': f'/audio/default_response.mp3'})

    query = generate_query(question)
    results = execute_query(query, patient_id)
    print(results)

    if not results:
        response_text = 'No data found or an error occurred.'
        audio_filepath = text_to_speech(response_text, "error.mp3")
        return jsonify({'response': response_text, 'audio_url': f'/audio/error.mp3'})

    if len(results) > 1 and not patient_id:
        response_text='Multiple patients found. Please provide the patient ID.'
        audio_filepath = text_to_speech(response_text, "multiple_patients.mp3")
        return jsonify({'response': response_text, 'audio_url': f'/audio/multiple_patients.mp3'})
    r=asizeof.asizeof(results)
    print(r)
    if r > 10000:
        response_text = generate_description(results)
        audio_filepath = text_to_speech(response_text, "detailed_response.mp3")
        return jsonify({'response': response_text, 'audio_url': f'/audio/detailed_response.mp3'})
    else:
        natural_language_output = convert_to_natural_language(results)
        audio_filepath = text_to_speech(natural_language_output, "response.mp3")
        return jsonify({'response': natural_language_output, 'audio_url': f'/audio/response.mp3'})


@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

from flask import Flask, render_template, request, redirect, url_for, session

import pandas as pd
import json

app.secret_key = '38219d9cedd2b5dfd5282df373c5c233'



# Load your CSV data (Structured data.csv)
data = pd.read_csv('structured_data.csv', encoding='ISO-8859-1')


def generate_description_patients_login(data_list):
    descriptions = []

    for data in data_list:
        description = ""

        # Basic Information
        description += f"Patient ID: {data['id']}\n"
        description += f"Name: {data['name']['first']} {data['name']['last']}\n"
        description += f"Age: {data['age']}\n"
        description += f"Date of Birth: {data['dob']}\n"
        description += f"Gender: {data['gender']}\n"
        description += f"Blood Group: {data['blood_group']}\n"
        description += f"Weight: {data['weight']}\n"

        # Contact Information
        contact = data['contact']
        address = contact['address']
        description += f"Contact Phone: {contact['phone']}\n"
        description += f"Address: {address['street']}, {address['city']}, {address['state']} {address['zip']}, {address['country']}\n"

        # Emergency Contact
        emergency_contact = data['emergency_contact']
        description += f"Emergency Contact: {emergency_contact['name']} ({emergency_contact['relationship']}) - {emergency_contact['phone']}\n"

        # Insurance Information
        insurance = data['insurance']
        description += f"Insurance Provider: {insurance['provider']}\n"
        description += f"Policy Number: {insurance['policy_number']}\n"
        description += f"Group Number: {insurance['group_number']}\n"
        description += f"Policy Effective Date: {insurance['effective_date']}\n"
        description += f"Policy Expiration Date: {insurance['expiration_date']}\n"
        nominee = insurance['nominee']
        description += f"Nominee: {nominee['name']} ({nominee['relationship']}) - {nominee['contact']}\n"

        # Claimed Insurance
        if 'claimed_insurance' in insurance and len(insurance['claimed_insurance']) > 0:
            description += "Claimed Insurance:\n"
            for claim in insurance['claimed_insurance']:
                description += f"  - Claim ID: {claim['claim_id']}, Date: {claim['date']}, Amount: {claim['amount']}, Status: {claim['status']}\n"

        # Medical History
        medical_history = data['medical_history']
        description += "Medical History:\n"
        if 'allergies' in medical_history:
            description += f"  Allergies: {', '.join(medical_history['allergies'])}\n"

        if 'conditions' in medical_history and len(medical_history['conditions']) > 0:
            description += "  Conditions:\n"
            for condition in medical_history['conditions']:
                description += f"    - {condition['name']} (Diagnosed on: {condition['diagnosed_date']}, Status: {condition['status']})\n"
        if 'surgeries' in medical_history and len(medical_history['surgeries']) > 0:
            description += "  Surgeries:\n"
            for surgery in medical_history['surgeries']:
                description += f"    - {surgery['name']} (Date: {surgery['date']}, Outcome: {surgery['outcome']})\n"
        if 'medications' in medical_history and len(medical_history['medications']) > 0:
            description += "  Medications:\n"
            for medication in medical_history['medications']:
                description += f"    - {medication['name']} (Dose: {medication['dose']}, Frequency: {medication['frequency']}, Start Date: {medication['start_date']})\n"

        # Appointments
        if 'appointments' in data and len(data['appointments']) > 0:
            description += "Appointments:\n"
            for appointment in data['appointments']:
                description += f"  - Date: {appointment['date']}, Type: {appointment['type']}\n"
                doctor = appointment['doctor']
                doctor_address = doctor['contact']['address']
                description += f"    Doctor: {doctor['name']} (Specialty: {doctor['specialty']})\n"
                description += f"    Contact: {doctor['contact']['phone']}, Address: {doctor_address['street']}, {doctor_address['city']}, {doctor_address['state']} {doctor_address['zip']}, {doctor_address['country']}\n"
                description += f"    Notes: {appointment['notes']}\n"

                # Lab Tests
                if 'lab_tests' in appointment and len(appointment['lab_tests']) > 0:
                    description += "    Lab Tests:\n"
                    for test in appointment['lab_tests']:
                        results = test['results']
                        description += f"      - Test: {test['test_name']} (Date: {test['date']})\n"
                        description += f"        Findings: {results.get('findings', 'N/A')}, Conclusion: {results.get('conclusion', 'N/A')}\n"

        # Test Results
        if 'test_results' in data and len(data['test_results']) > 0:
            description += "Test Results:\n"
            for test_result in data['test_results']:
                results = test_result['results']
                description += f"  - Test: {test_result['test_name']} (Date: {test_result['date']})\n"
                description += f"    Findings: {results['findings']}, Conclusion: {results['conclusion']}\n"

        # Health Monitoring
        if 'health_monitoring' in data and 'daily_vitals' in data['health_monitoring']:
            description += "Daily Vitals:\n"
            for vitals in data['health_monitoring']['daily_vitals']:
                description += f"  - Date: {vitals['date']}, Blood Pressure: {vitals['blood_pressure']}, Heart Rate: {vitals['heart_rate']}, Temperature: {vitals['temperature']}°F\n"

        descriptions.append(description)
    print(descriptions)

    return "\n\n".join(descriptions)

# Function to authenticate users
def authenticate_user(role, username, password):
    username = username.strip()
    password = password.strip()
    print(username,password)
    
    if role == 'patient':
        user_data = data[(data['full_name'].str.strip().str.lower() == username.lower()) & 
                         (data['dob'].astype(str).str.strip() == password)]
    elif role == 'doctor':
        user_data = data[(data['doctor_name'].str.strip().str.lower() == username.lower()) & 
                         (data['doc_id'].astype(str).str.strip() == password)]
    elif role == 'insurance':
        user_data = data[(data['insurance_provider'].str.strip().str.lower() == username.lower()) & 
                         (data['insurance_id'].astype(str).str.strip() == password)]

    return not user_data.empty

@app.route('/')
def index():
    return render_template('login.html')

from bson import ObjectId

def convert_object_ids(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, ObjectId):
                obj[key] = str(value)
            elif isinstance(value, (dict, list)):
                obj[key] = convert_object_ids(value)
    elif isinstance(obj, list):
        obj = [convert_object_ids(item) if isinstance(item, (dict, list)) else item for item in obj]
    return obj

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if authenticate_user(role, username, password):
            session['username'] = username
            session['role'] = role
            session['password'] = password

            if role == 'patient':
                name_parts = username.split(" ")
                if len(name_parts) != 2:
                    return "Invalid username format. Please use 'First Last'."

                first_name, last_name = name_parts
                formatted_dob = f"{password[:4]}-{password[4:6]}-{password[6:]}"

            # Query MongoDB for the patient record
                patient_record = collection.find_one({
                "name.first": first_name,
                "name.last": last_name,
                "dob": formatted_dob
            },{"_id":0})

                if patient_record:
                # Convert all ObjectIds to strings
                #patient_record=generate_description_patients_login(patient_record)
                    print(patient_record)

                    return render_template('patient.html', patient=patient_record)
            else:
                return redirect(url_for('index1'))

        else:
            return "Invalid credentials. Please try again."
    return render_template('login.html')

@app.route('/index1')
def index1():
    return render_template('index1.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


