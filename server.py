import src.main as formatter
import src.document as mydoc
from flask import Flask, request, send_file, render_template_string, after_this_request
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import tempfile
from docx import Document
import io
from pathlib import Path
from version import get_version_info

app = Flask(__name__)
CORS(app, expose_headers=['Content-Disposition', 'Content-Type'])

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'docx'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getCommitteeShortened(committee: str) -> str:
    result = {
        "environment programme": "unep",
        "un environment programme": "unep",
        "environment programme (unep)": "unep",
        "un environment programme (unep)": "unep",
        "environment programme(unep)": "unep",
        "un environment programme(unep)": "unep",

        "united nations environment programme": "unep",
        "united nations environment programme (unep)": "unep",
        "environment programme(unep)": "unep",
        "united nations environment programme(unep)": "unep",
        
        "historical human rights council": "hhrc",
        "human rights council": "hrc",
        "historical human rights council (hhrc)": "hhrc",
        "human rights council (hrc)": "hrc",
        "historical human rights council(hhrc)": "hhrc",
        "human rights council(hrc)": "hrc",
        
        "united nations historical human rights council": "hhrc",
        "united nations human rights council": "hrc",
        "united nations historical human rights council (hhrc)": "hhrc",
        "united nations human rights council (hrc)": "hrc",
        "united nations historical human rights council(hhrc)": "hhrc",
        "united nations human rights council(hrc)": "hrc",
        
        "general assembly": "ga",
        "united nations general assembly": "ga",
        "general assembly (ga)": "ga",
        "united nations general assembly (ga)": "ga",
        "general assembly (unga)": "ga",
        "united nations general assembly (unga)": "ga",
        "general assembly(ga)": "ga",
        "united nations general assembly(ga)": "ga",
        "general assembly(unga)": "ga",
        "united nations general assembly(unga)": "ga",
        
        "general assembly": "ga",
        "un general assembly": "ga",
        "general assembly (ga)": "ga",
        "un general assembly (ga)": "ga",
        "general assembly (unga)": "ga",
        "un general assembly (unga)": "ga",
        "general assembly(ga)": "ga",
        "un general assembly(ga)": "ga",
        "general assembly(unga)": "ga",
        "un general assembly(unga)": "ga",

        "security council": "sc",
        "united nations security council": "sc",
        "security council (unsc)": "sc",
        "united nations security council (unsc)": "sc",
        "security council": "sc",
        "un security council": "sc",
        "security council (unsc)": "sc",
        "un security council (unsc)": "sc"
    }.get(committee.lower())
    
    
    if result is not None:
        return result.upper()
    # print("Unable to get shorthand for committee:", committee)
    return committee

def process_document(filename: str) -> tuple[str, str]:
    d = mydoc.document(str(Path(filename)), str(Path(filename)))
    parseResult = formatter.parseToResolution(d)
    parsedResolution, components, errorList = parseResult
    mainSub = parsedResolution.mainSubmitter
    cmt = getCommitteeShortened(parsedResolution.committee)
    formatter.writeToFile(parsedResolution, filename)
    return mainSub, cmt

@app.route('/')
def index():
    version_info = get_version_info()
    return f"Backend is running! Use /upload to upload files.\n\n{version_info}"

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if file was uploaded
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    
    file = request.files['file']
    
    # Check if file was selected
    if file.filename == '' or file.filename is None:
        return {'error': 'No selected file'}, 400
    
    # Check if it's a docx file
    if not allowed_file(file.filename):
        return {'error': 'File type not allowed. Please upload .docx files only'}, 400
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        file.save(temp_input.name)
        temp_input.close()
        
        # Process the document
        mainSub, cmt = process_document(temp_input.name)
        
        # Send the processed file back to user
        @after_this_request
        def cleanup(response):
            try:
                os.unlink(temp_input.name)
            except Exception as e:
                app.logger.error(f"Error deleting temp file: {e}")
            return response
        custom_filename = f"DR_{mainSub}_{cmt}"
        response = send_file(
            temp_input.name,
            as_attachment=True,
            download_name=custom_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{custom_filename}"'
        return response
        
    except Exception as e:
        return {'error': str(e)}, 500
    
    finally:
        # Clean up temporary files
        try:
            os.unlink(temp_input.name) # type: ignore
        except:
            pass

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)