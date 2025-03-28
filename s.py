from flask import Flask, request, jsonify
from pytesseract import pytesseract
from pdfminer.high_level import extract_text
from io import BytesIO
from PIL import Image
import google.generativeai as genai

app = Flask(__name__)

# ✅ Set up Gemini API key
genai.configure(api_key="your GEMINI API")

# ✅ Use the correct model name
MODEL_NAME = "gemini-1.5-pro-latest"

# Path to Tesseract executable
pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Discharge Report Summarizer</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <style>
            body {
                background-color: #f8f9fa;
                font-family: 'Arial', sans-serif;
            }
            h1 {
                color: #007bff;
            }
            .upload-box {
                border: 2px dashed #007bff;
                padding: 20px;
                border-radius: 10px;
                background-color: #ffffff;
                cursor: pointer;
                transition: 0.3s;
                text-align: center;
            }
            .upload-box:hover {
                background-color: #e9f5ff;
            }
            .upload-label {
                font-size: 18px;
                font-weight: bold;
                color: #007bff;
            }
            .result-box {
                background-color: #ffffff;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #007bff;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                margin-top: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
            }
            th {
                background-color: #007bff;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>

        <div class="container">
            <h1 class="text-center mt-4">📝 Discharge Report Summarizer</h1>
            <p class="text-center text-muted">Upload an image or PDF file to extract and summarize key medical details.</p>

            <div class="upload-box" onclick="document.getElementById('fileInput').click()">
                <input type="file" id="fileInput" name="files" multiple hidden>
                <p class="upload-label">📂 Click or Drag & Drop Files Here</p>
                <p class="text-muted">Supported formats: PNG, JPG, PDF</p>
            </div>

            <button id="uploadBtn" class="btn btn-primary w-100 mt-3">Extract & Summarize</button>

            <div id="resultContainer" class="result-box">
                <h5>🩺 Patient Report:</h5>
                <div id="tableContainer"></div>
            </div>
        </div>

        <script>
            $(document).ready(function() {
                $("#uploadBtn").click(function() {
                    let formData = new FormData();
                    let files = $("#fileInput")[0].files;
                    
                    if (files.length === 0) {
                        alert("Please select a file.");
                        return;
                    }

                    for (let i = 0; i < files.length; i++) {
                        formData.append("files", files[i]);
                    }

                    $.ajax({
                        url: "/extract_text1",
                        type: "POST",
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(response) {
                            $("#tableContainer").html(response);
                        },
                        error: function(xhr) {
                            alert("Error processing file.");
                        }
                    });
                });
            });
        </script>

    </body>
    </html>
    """

@app.route('/extract_text1', methods=['POST'])
def extract_text1():
    prompt = ("Extract the patient details from the given medical report and return a proper HTML table with the following columns: "
          "**Patient Name, Age, Gender, Diagnosis (Medical condition or illness), Treatment (Prescribed procedures, medications, or therapy), Admitted Date, Follow-up Date.** "
          "Ensure the output is a clean, structured `<table>` without any Markdown or code formatting. "
          "Do NOT wrap the table inside ```html or any other code block. "
          "If gender value is missing, infer it using the patient’s name if possible. "
          "If no information is available, leave the field blank but keep the table structure intact.")

    files = request.files.getlist('files')
    results = []

    for file in files:
        if file.filename.endswith('.pdf'):
            try:
                with BytesIO(file.read()) as file_stream:
                    pdf_text = extract_text(file_stream)
                report = pdf_text
            except Exception as e:
                return jsonify({'message': 'Error processing PDF:', 'error': str(e)}), 500
        else:
            try:
                image_text = pytesseract.image_to_string(Image.open(file))
                report = image_text
            except Exception as e:
                return jsonify({'message': 'Error processing image:', 'error': str(e)}), 500
        
        try:
            # ✅ Use the correct model name
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content(report + "\n\n" + prompt)
            results.append(response.text)
        except Exception as e:
            return jsonify({'message': 'Error summarizing text:', 'error': str(e)}), 500

    return results[-1] if results else jsonify({'message': 'No text extracted.'})

if __name__ == '__main__':
    app.run(debug=True)
