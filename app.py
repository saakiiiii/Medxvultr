from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
from pymongo import MongoClient
from urllib.parse import quote_plus
from werkzeug.utils import secure_filename
from bson.binary import Binary
from time import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from fpdf import FPDF
import threading
import json

from model.dummy_model import check_medicine_quality  # type: ignore
from utils.auth_utils import login_user, logout_user, require_login
from utils.generate_code import generate_unique_code
from utils.tracking_api import get_tracking_status
from database.db import mongo
from config import config
from textExtract import main  # Assuming this is your text extraction module

app = Flask(__name__)
CORS(app)
app.config.from_object(config)
mongo.init_app(app)

username = quote_plus('dave')
password = quote_plus('passwordfordb')
uri = f"mongodb+srv://{username}:{password}@cluster0.mwh6h.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['UserData']
collection = db['UserCredentials']
collectionP = db['Patients']

@app.route("/")
def suggest_me():
    return "Hello World!"
#authentication
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = login_user(data.get("username"), data.get("password"))
    if user:
        session['user_id'] = user["_id"]
        return jsonify({"message": "Logged in successfully"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
@require_login
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200
#quality check
@app.route('/check-quality', methods=['POST'])
@require_login
def check_quality():
    data = request.json
    medicine_data = data.get('medicine_data')
    unique_code = generate_unique_code()
    quality_status = check_medicine_quality(medicine_data)

    mongo.db.medicines.insert_one({
        "unique_code": unique_code,
        "medicine_data": medicine_data,
        "quality_status": quality_status,
        "tracking_status": "In transit",
        "verified": False
    })

    return jsonify({"unique_code": unique_code, "quality_status": quality_status}), 200
# tracking
@app.route('/track', methods=['GET'])
@require_login
def track():
    unique_code = request.args.get('unique_code')
    medicine = mongo.db.medicines.find_one({"unique_code": unique_code})
    if medicine:
        tracking_status = get_tracking_status(unique_code)
        mongo.db.medicines.update_one(
            {"unique_code": unique_code},
            {"$set": {"tracking_status": tracking_status}}
        )
        return jsonify({
            "unique_code": unique_code,
            "tracking_status": tracking_status
        }), 200
    return jsonify({"error": "Invalid code"}), 404
#verifivation
@app.route('/verify', methods=['POST'])
@require_login
def verify_medicine():
    unique_code = request.json.get("unique_code")
    medicine = mongo.db.medicines.find_one({"unique_code": unique_code})
    if medicine:
        mongo.db.medicines.update_one(
            {"unique_code": unique_code},
            {"$set": {"verified": True}}
        )
        return jsonify({"message": "Medicine verified successfully"}), 200
    return jsonify({"error": "Invalid code"}), 404

# PDF Handling and Management Functions
def handle_file_upload(file, name):
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file_data = file.read()
        binary_file_data = Binary(file_data)

        # Save file data in MongoDB for the patient
        collectionP.update_one(
            {'name': name},
            {'$push': {'pdfs': {'filename': filename, 'upload_date': time(), 'data': binary_file_data, 'response': main()}}}
        )
        print("File uploaded successfully")
    else:
        print("Invalid file type")

@app.route("/uploadpdf", methods=['POST'])
def uploadpdf():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    name = request.form.get('name').lower()
    if not name:
        return jsonify({"message": "No name provided"}), 400

    # Create patient if they don't exist
    if collectionP.find_one({'name': name}) is None:
        collectionP.insert_one({'name': name, 'pdfs': []})

    if file and file.filename.endswith('.pdf'):
        # Process file upload in a separate thread
        thread = threading.Thread(target=handle_file_upload, args=(file, name))
        thread.start()
        return jsonify({"message": "File uploaded successfully"}), 201
    else:
        return jsonify({"message": "Invalid file type"}), 400

@app.route("/getpdfs", methods=['GET'])
def getpdfs():
    name = request.args.get('name')
    pdfNames = []
    pat = collectionP.find_one({'name': name})
    if pat is not None:
        for pdf in pat['pdfs']:
            pdfNames.append(pdf['filename'])
        return jsonify({"pdfs": pdfNames}), 200
    else:
        return jsonify({"pdfs": pdfNames, "message": "Patient not found"}), 404

@app.route("/getpdf", methods=['GET'])
def getpdf():
    name = request.args.get('name')
    pdfName = request.args.get('pdfName')
    patient = collectionP.find_one({'name': name})
    bodyText = "The file was not converted successfully"

    if patient is not None:
        for pdf in patient['pdfs']:
            if pdf['filename'] == pdfName:
                with open("input.pdf", "wb") as f:
                    f.write(pdf['data'])
                bodyText = pdf['response']
                if len(bodyText) >= 2:
                    bodyText = create_printable_string(bodyText)
                elif len(bodyText) == 1:
                    bodyText = bodyText[0]
                break
        create_and_append_pdf(bodyText, "input.pdf", "lib/download.pdf")
        return jsonify({"bodytext": bodyText})
    else:
        return jsonify({"bodytext": "Patient not found"})

@app.route("/downloadpdf", methods=['GET'])
def downloadpdf():
    return send_file("lib/download.pdf", as_attachment=True)

# PDF Helper Functions
def create_printable_string(bodyText):
    printable_string = bodyText[0] + "\n\n"
    printable_string += "Medications:\n"
    c = ""
    line = ""
    counter = 1
    debug = ""
    for i in bodyText[1]:
        if i == '"' and len(c) == 0:
            c += "1"
        elif i == '"' and len(c) > 0:
            c = c[1:]
            if len(line) == 0:
                line = f"{counter}. {c} - "
                counter += 1
            else:
                line += c + "\n"
                debug += line
                line = ""
            c = ""
        elif len(c) > 0:
            c += i
    printable_string += debug
    if len(bodyText) > 2:
        printable_string += "\n" + bodyText[2]
    return printable_string

def create_pdf_from_string(text, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=15)
    with open("myfile.txt", "w") as f:
        f.write(text)
    with open("myfile.txt", "r") as f:
        for line in f:
            pdf.multi_cell(0, 10, txt=line, align='L')
    pdf.output(output_path)

def append_pdfs(input_pdf_path, output_pdf_path, appended_pdf_path):
    pdf_writer = PdfWriter()
    input_pdf = PdfReader(input_pdf_path)
    for page_num in range(len(input_pdf.pages)):
        page = input_pdf.pages[page_num]
        pdf_writer.add_page(page)
    appended_pdf = PdfReader(appended_pdf_path)
    for page_num in range(len(appended_pdf.pages)):
        page = appended_pdf.pages[page_num]
        pdf_writer.add_page(page)
    with open(output_pdf_path, 'wb') as out_pdf:
        pdf_writer.write(out_pdf)

def create_and_append_pdf(text, input_pdf_path, output_pdf_path):
    temp_pdf_path = "temp.pdf"
    create_pdf_from_string(text, temp_pdf_path)
    append_pdfs(input_pdf_path, output_pdf_path, temp_pdf_path)

if __name__ == "__main__":
    app.secret_key = app.config["SECRET_KEY"]
    app.run(debug=True)
