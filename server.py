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
CORS(app)  # This allows your frontend to talk to backend

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'docx'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_document(filename: str):
    
    d = mydoc.document(str(Path(filename)), str(Path(filename)))
    parseResult = formatter.parseToResolution(d)
    parsedResolution, components, errorList = parseResult
    formatter.writeToFile(parsedResolution, filename)

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
        process_document(temp_input.name)        
        
        
        
        # Send the processed file back to user
        @after_this_request
        def cleanup(response):
            try:
                os.unlink(temp_input.name)
            except Exception as e:
                app.logger.error(f"Error deleting temp file: {e}")
            return response

        return send_file(
            temp_input.name,
            as_attachment=True,
            download_name=f"Formatted_{filename}",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
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