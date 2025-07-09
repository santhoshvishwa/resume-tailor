from flask import Flask, request, jsonify, render_template_string
import os
import requests
import json
from docx import Document
import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resume Tailor</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                max-width: 900px; 
                margin: 0 auto; 
                padding: 20px; 
                background: #f8f9fa;
            }
            .container {
                background: white;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .upload-area { 
                border: 2px dashed #3498db; 
                padding: 30px; 
                text-align: center; 
                margin: 20px 0; 
                border-radius: 8px;
                background: #f8f9ff;
            }
            .form-group {
                margin: 20px 0;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #2c3e50;
            }
            input[type="file"] {
                width: 100%;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-family: inherit;
                resize: vertical;
                background: white;
            }
            .error { 
                color: #e74c3c; 
                background: #ffebee; 
                padding: 15px; 
                border-radius: 4px; 
                margin: 10px 0; 
                border-left: 4px solid #e74c3c;
            }
            .success { 
                color: #27ae60; 
                background: #e8f5e9; 
                padding: 15px; 
                border-radius: 4px; 
                margin: 10px 0; 
                border-left: 4px solid #27ae60;
            }
            .loading { 
                display: none; 
                text-align: center;
                padding: 20px;
                color: #3498db;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            button { 
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white; 
                border: none; 
                padding: 12px 30px; 
                border-radius: 6px; 
                cursor: pointer; 
                font-size: 16px;
                width: 100%;
                transition: all 0.3s ease;
            }
            button:hover {
                background: linear-gradient(135deg, #2980b9, #3498db);
                transform: translateY(-2px);
            }
            button:disabled { 
                background: #bdc3c7; 
                cursor: not-allowed; 
                transform: none;
            }
            .result-container {
                margin-top: 20px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
            .suggestion-item {
                background: white;
                margin: 10px 0;
                padding: 15px;
                border-radius: 6px;
                border-left: 4px solid #3498db;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Resume Tailor</h1>
            <p style="text-align: center; color: #7f8c8d; margin-bottom: 30px;">
                Optimize your resume to match job requirements perfectly
            </p>
            
            <div class="upload-area">
                <div class="form-group">
                    <label for="resume">📄 Upload Your Resume</label>
                    <input type="file" id="resume" accept=".docx,.txt" required>
                </div>
                
                <div class="form-group">
                    <label for="jobDescription">📋 Job Description</label>
                    <textarea id="jobDescription" placeholder="Paste the job description here..." rows="6" required></textarea>
                </div>
                
                <button onclick="uploadFiles()">✨ Tailor My Resume</button>
            </div>
            
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Analyzing your resume and job description...</p>
            </div>
            
            <div id="result"></div>
        </div>

        <script>
            async function uploadFiles() {
                const fileInput = document.getElementById('resume');
                const jobDescription = document.getElementById('jobDescription').value;
                const loading = document.getElementById('loading');
                const result = document.getElementById('result');
                const button = document.querySelector('button');
                
                if (!fileInput.files[0] || !jobDescription.trim()) {
                    result.innerHTML = '<div class="error">❌ Please select a resume file and enter a job description.</div>';
                    return;
                }
                
                const formData = new FormData();
                formData.append('resume', fileInput.files[0]);
                formData.append('job_description', jobDescription);
                
                loading.style.display = 'block';
                button.disabled = true;
                result.innerHTML = '';
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        result.innerHTML = `
                            <div class="success">✅ Resume analysis completed!</div>
                            <div class="result-container">
                                <h3>📊 Tailoring Suggestions:</h3>
                                <div style="white-space: pre-wrap; line-height: 1.6;">${data.suggestions}</div>
                            </div>
                        `;
                    } else {
                        result.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                    }
                } catch (error) {
                    result.innerHTML = `<div class="error">❌ Network error: ${error.message}</div>`;
                } finally {
                    loading.style.display = 'none';
                    button.disabled = false;
                }
            }
        </script>
    </body>
    </html>
    ''')

def extract_text_from_docx(file_stream):
    """Extract text from DOCX file"""
    try:
        doc = Document(file_stream)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    except Exception as e:
        raise Exception(f"Error reading DOCX file: {str(e)}")

def extract_keywords(text):
    """Extract key skills and keywords from text"""
    # Common skill patterns
    skills_patterns = [
        r'\b(?:Python|Java|JavaScript|React|Angular|Vue|Node\.js|Django|Flask|Spring|SQL|MongoDB|PostgreSQL|MySQL|AWS|Azure|GCP|Docker|Kubernetes|Git|CI/CD|REST|API|HTML|CSS|TypeScript|C\+\+|C#|Ruby|PHP|Go|Rust|Scala|Machine Learning|AI|Data Science|Analytics|Tableau|Power BI|Excel|Leadership|Management|Communication|Problem Solving|Agile|Scrum|DevOps|Testing|QA|UX|UI|Product Management|Project Management|Marketing|Sales|Customer Service|Finance|Accounting|HR|Operations|Strategy|Business Analysis|Data Analysis|Research|Writing|Design|Creative|Photoshop|Illustrator|Figma|Sketch)\b',
        r'\b\w+(?:\s+\w+)*(?:\s+(?:experience|skills?|knowledge|expertise|proficiency|certification|certified|degree|bachelor|master|phd|years?|months?))\b',
        r'\b(?:experience|skilled?|proficient|expert|knowledge|familiar|understanding|background|expertise)\s+(?:in|with|of)\s+\w+(?:\s+\w+)*\b'
    ]
    
    keywords = set()
    for pattern in skills_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.update(matches)
    
    return list(keywords)

def analyze_resume_match(resume_text, job_description):
    """Analyze how well the resume matches the job description"""
    resume_keywords = set(extract_keywords(resume_text.lower()))
    job_keywords = set(extract_keywords(job_description.lower()))
    
    # Find matching and missing keywords
    matching_keywords = resume_keywords.intersection(job_keywords)
    missing_keywords = job_keywords - resume_keywords
    
    # Calculate match score
    if len(job_keywords) > 0:
        match_score = len(matching_keywords) / len(job_keywords) * 100
    else:
        match_score = 0
    
    return {
        'match_score': match_score,
        'matching_keywords': list(matching_keywords),
        'missing_keywords': list(missing_keywords),
        'job_keywords': list(job_keywords)
    }

def generate_suggestions(resume_text, job_description, analysis):
    """Generate tailoring suggestions based on analysis"""
    suggestions = []
    
    # Header suggestion
    suggestions.append("📊 MATCH ANALYSIS")
    suggestions.append(f"Current match score: {analysis['match_score']:.1f}%")
    suggestions.append("")
    
    # Missing keywords section
    if analysis['missing_keywords']:
        suggestions.append("🔍 MISSING KEYWORDS TO ADD:")
        for keyword in analysis['missing_keywords'][:10]:  # Top 10 missing keywords
            suggestions.append(f"• {keyword}")
        suggestions.append("")
    
    # Matching keywords section
    if analysis['matching_keywords']:
        suggestions.append("✅ KEYWORDS YOU'RE ALREADY USING:")
        for keyword in analysis['matching_keywords'][:8]:  # Top 8 matching keywords
            suggestions.append(f"• {keyword}")
        suggestions.append("")
    
    # Section-specific suggestions
    suggestions.append("📝 SECTION-SPECIFIC IMPROVEMENTS:")
    
    # Skills section
    suggestions.append("• SKILLS SECTION:")
    suggestions.append("  - Add technical skills mentioned in job description")
    suggestions.append("  - Group skills by category (Technical, Soft Skills, Tools)")
    suggestions.append("  - Prioritize skills mentioned in job requirements")
    suggestions.append("")
    
    # Experience section
    suggestions.append("• EXPERIENCE SECTION:")
    suggestions.append("  - Use action verbs (Developed, Implemented, Managed, Led)")
    suggestions.append("  - Quantify achievements with numbers and percentages")
    suggestions.append("  - Match your experience descriptions to job requirements")
    suggestions.append("  - Highlight relevant projects and accomplishments")
    suggestions.append("")
    
    # General improvements
    suggestions.append("🎯 GENERAL IMPROVEMENTS:")
    suggestions.append("• Customize your professional summary to match the role")
    suggestions.append("• Use industry-specific terminology from the job posting")
    suggestions.append("• Ensure your resume passes ATS (Applicant Tracking System)")
    suggestions.append("• Keep formatting clean and professional")
    suggestions.append("• Use consistent verb tenses")
    suggestions.append("")
    
    # Action items
    suggestions.append("📋 ACTION ITEMS:")
    suggestions.append("1. Add missing keywords naturally throughout your resume")
    suggestions.append("2. Reorder sections to highlight most relevant experience first")
    suggestions.append("3. Quantify achievements with specific numbers/percentages")
    suggestions.append("4. Tailor your professional summary to this specific role")
    suggestions.append("5. Review and update your skills section")
    
    return "\n".join(suggestions)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check if files are present
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        if 'job_description' not in request.form:
            return jsonify({'error': 'No job description provided'}), 400
        
        resume_file = request.files['resume']
        job_description = request.form['job_description']
        
        if resume_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not job_description.strip():
            return jsonify({'error': 'Job description cannot be empty'}), 400
        
        # Extract text from resume
        if resume_file.filename.endswith('.docx'):
            resume_text = extract_text_from_docx(resume_file)
        elif resume_file.filename.endswith('.txt'):
            resume_text = resume_file.read().decode('utf-8')
        else:
            return jsonify({'error': 'Unsupported file format. Please use .docx or .txt files.'}), 400
        
        # Analyze resume against job description
        analysis = analyze_resume_match(resume_text, job_description)
        
        # Generate suggestions
        suggestions = generate_suggestions(resume_text, job_description, analysis)
        
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
