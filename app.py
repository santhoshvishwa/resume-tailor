from flask import Flask, render_template, request, jsonify, send_file
import os
import openai
from docx import Document
import tempfile
import io
from datetime import datetime
import re
import json
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure OpenAI
openai.api_key = os.environ.get('OPENAI_API_KEY')

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_docx(file_path):
    """Extract text content from a .docx file"""
    try:
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    except Exception as e:
        print(f"Error reading docx file: {e}")
        return None

def extract_text_from_txt(file_path):
    """Extract text content from a .txt file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading txt file: {e}")
        return None

def create_tailoring_prompt(resume_text, job_description):
    """Create a comprehensive prompt for resume tailoring"""
    prompt = f"""
You are an expert resume writer and ATS optimization specialist. Please rewrite the following resume to be perfectly tailored for the job description provided. Follow these guidelines:

1. KEYWORD OPTIMIZATION:
   - Identify key skills, technologies, and requirements from the job description
   - Naturally incorporate these keywords throughout the resume
   - Ensure keyword density is appropriate for ATS systems

2. SUMMARY/OBJECTIVE REWRITE:
   - Rewrite the professional summary to directly address the job requirements
   - Highlight the most relevant experience and skills
   - Use compelling language that matches the job posting tone

3. EXPERIENCE ENHANCEMENT:
   - Reorder and rewrite bullet points to emphasize relevant experience
   - Use strong action verbs and quantify achievements where possible
   - Focus on accomplishments that align with job requirements

4. SKILLS OPTIMIZATION:
   - Prioritize technical and soft skills mentioned in the job description
   - Remove irrelevant skills that don't match the position
   - Add any missing relevant skills the candidate likely has

5. ATS FORMATTING:
   - Use standard section headers (Experience, Education, Skills, etc.)
   - Avoid complex formatting, tables, or graphics
   - Use consistent bullet points and formatting

6. MAINTAIN AUTHENTICITY:
   - Keep all information truthful and accurate
   - Don't add experience or skills the candidate doesn't have
   - Preserve the candidate's voice and career progression

JOB DESCRIPTION:
{job_description}

ORIGINAL RESUME:
{resume_text}

Please provide the tailored resume in a clean, professional format that will perform well in ATS systems. Return only the optimized resume content without any additional commentary.
"""
    return prompt

def call_openai_api(prompt):
    """Call OpenAI API to get tailored resume"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer and ATS optimization specialist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

def create_docx_from_text(text, original_docx_path=None):
    """Create a new .docx file from text, preserving basic formatting"""
    try:
        # Create a new document
        doc = Document()
        
        # Add title styling
        title_style = doc.styles['Heading 1']
        
        # Split text into sections and paragraphs
        sections = text.split('\n\n')
        
        for section in sections:
            if section.strip():
                lines = section.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line:
                        # Check if this looks like a section header
                        if (line.isupper() or 
                            any(header in line.upper() for header in ['EXPERIENCE', 'EDUCATION', 'SKILLS', 'SUMMARY', 'OBJECTIVE', 'CONTACT'])):
                            # Add as heading
                            doc.add_heading(line, level=1)
                        else:
                            # Add as regular paragraph
                            paragraph = doc.add_paragraph(line)
                            
                            # Add bullet formatting if line starts with bullet-like characters
                            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                                paragraph.style = 'List Bullet'
        
        # Save to bytes
        doc_bytes = io.BytesIO()
        doc.save(doc_bytes)
        doc_bytes.seek(0)
        
        return doc_bytes
    except Exception as e:
        print(f"Error creating docx: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'resume' not in request.files or 'job_description' not in request.files:
        return jsonify({'error': 'Both resume and job description files are required'}), 400
    
    resume_file = request.files['resume']
    job_file = request.files['job_description']
    
    if resume_file.filename == '' or job_file.filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    if not (allowed_file(resume_file.filename) and allowed_file(job_file.filename)):
        return jsonify({'error': 'Invalid file type. Please upload .docx for resume and .txt for job description'}), 400
    
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded files
        resume_filename = secure_filename(f"{session_id}_resume.docx")
        job_filename = secure_filename(f"{session_id}_job.txt")
        
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
        job_path = os.path.join(app.config['UPLOAD_FOLDER'], job_filename)
        
        resume_file.save(resume_path)
        job_file.save(job_path)
        
        # Extract text from files
        resume_text = extract_text_from_docx(resume_path)
        job_text = extract_text_from_txt(job_path)
        
        if not resume_text or not job_text:
            return jsonify({'error': 'Failed to extract text from uploaded files'}), 400
        
        # Create tailoring prompt
        prompt = create_tailoring_prompt(resume_text, job_text)
        
        # Call OpenAI API
        tailored_resume = call_openai_api(prompt)
        
        if not tailored_resume:
            return jsonify({'error': 'Failed to generate tailored resume'}), 500
        
        # Create new .docx file
        output_docx = create_docx_from_text(tailored_resume, resume_path)
        
        if not output_docx:
            return jsonify({'error': 'Failed to create output document'}), 500
        
        # Save the output file
        output_filename = f"{session_id}_tailored_resume.docx"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        with open(output_path, 'wb') as f:
            f.write(output_docx.getvalue())
        
        # Clean up input files
        os.remove(resume_path)
        os.remove(job_path)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Resume tailored successfully!',
            'download_url': f'/download/{session_id}'
        })
        
    except Exception as e:
        print(f"Error processing files: {e}")
        return jsonify({'error': 'An error occurred while processing your files'}), 500

@app.route('/download/<session_id>')
def download_file(session_id):
    try:
        filename = f"{session_id}_tailored_resume.docx"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        def remove_file_after_send(response):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error removing file: {e}")
            return response
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"tailored_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        print(f"Error downloading file: {e}")
        return jsonify({'error': 'Error downloading file'}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=os.environ.get('DEBUG', 'False').lower() == 'true', 
            host='0.0.0.0', 
            port=port)
