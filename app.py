from flask import Flask, request, jsonify, render_template_string
import os
import re
from docx import Document
import json

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
                max-width: 1200px; 
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
            .resume-output {
                margin-top: 20px;
                padding: 30px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-family: 'Times New Roman', serif;
                line-height: 1.6;
                color: #333;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .resume-header {
                text-align: center;
                border-bottom: 2px solid #3498db;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            .resume-name {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            .resume-contact {
                color: #7f8c8d;
                font-size: 14px;
            }
            .resume-section {
                margin-bottom: 25px;
            }
            .section-title {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                border-bottom: 1px solid #bdc3c7;
                padding-bottom: 5px;
                margin-bottom: 15px;
                text-transform: uppercase;
            }
            .job-entry {
                margin-bottom: 20px;
            }
            .job-title {
                font-weight: bold;
                color: #2c3e50;
            }
            .job-company {
                font-style: italic;
                color: #7f8c8d;
            }
            .job-date {
                float: right;
                color: #7f8c8d;
                font-size: 14px;
            }
            .job-description {
                margin-top: 8px;
            }
            .skills-list {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }
            .skill-item {
                background: #ecf0f1;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 14px;
                color: #2c3e50;
            }
            .download-btn {
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                margin-top: 20px;
                font-size: 14px;
            }
            .download-btn:hover {
                background: #219a52;
            }
            .copy-btn {
                background: #f39c12;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                margin-left: 10px;
                font-size: 14px;
            }
            .copy-btn:hover {
                background: #d68910;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Resume Tailor</h1>
            <p style="text-align: center; color: #7f8c8d; margin-bottom: 30px;">
                Generate a perfectly tailored resume that matches the job description
            </p>
            
            <div class="upload-area">
                <div class="form-group">
                    <label for="resume">📄 Upload Your Current Resume</label>
                    <input type="file" id="resume" accept=".docx,.txt" required>
                </div>
                
                <div class="form-group">
                    <label for="jobDescription">📋 Job Description</label>
                    <textarea id="jobDescription" placeholder="Paste the complete job description here..." rows="8" required></textarea>
                </div>
                
                <button onclick="generateResume()">✨ Generate Tailored Resume</button>
            </div>
            
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Analyzing and tailoring your resume...</p>
            </div>
            
            <div id="result"></div>
        </div>

        <script>
            async function generateResume() {
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
                    const response = await fetch('/generate', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        result.innerHTML = `
                            <div class="success">✅ Tailored resume generated successfully!</div>
                            <div class="resume-output" id="resumeOutput">
                                ${data.tailored_resume}
                            </div>
                            <div style="text-align: center; margin-top: 20px;">
                                <button class="copy-btn" onclick="copyToClipboard()">📋 Copy Resume</button>
                                <button class="download-btn" onclick="downloadResume()">💾 Download as Text</button>
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
            
            function copyToClipboard() {
                const resumeText = document.getElementById('resumeOutput').innerText;
                navigator.clipboard.writeText(resumeText).then(() => {
                    alert('Resume copied to clipboard!');
                });
            }
            
            function downloadResume() {
                const resumeText = document.getElementById('resumeOutput').innerText;
                const blob = new Blob([resumeText], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'tailored_resume.txt';
                a.click();
                URL.revokeObjectURL(url);
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

def parse_resume_sections(resume_text):
    """Parse resume into structured sections"""
    sections = {
        'contact': '',
        'summary': '',
        'experience': [],
        'education': [],
        'skills': [],
        'other': []
    }
    
    lines = resume_text.split('\n')
    current_section = 'other'
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect section headers
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['experience', 'work', 'employment', 'career']):
            if current_content:
                sections[current_section].extend(current_content)
            current_section = 'experience'
            current_content = []
        elif any(keyword in line_lower for keyword in ['education', 'academic', 'degree']):
            if current_content:
                sections[current_section].extend(current_content)
            current_section = 'education'
            current_content = []
        elif any(keyword in line_lower for keyword in ['skills', 'technical', 'competencies']):
            if current_content:
                sections[current_section].extend(current_content)
            current_section = 'skills'
            current_content = []
        elif any(keyword in line_lower for keyword in ['summary', 'profile', 'objective']):
            if current_content:
                sections[current_section].extend(current_content)
            current_section = 'summary'
            current_content = []
        elif '@' in line or any(keyword in line_lower for keyword in ['phone', 'email', 'address']):
            sections['contact'] = line
        else:
            current_content.append(line)
    
    # Add remaining content
    if current_content:
        sections[current_section].extend(current_content)
    
    return sections

def extract_job_requirements(job_description):
    """Extract key requirements from job description"""
    requirements = {
        'skills': [],
        'experience_years': '',
        'education': '',
        'key_responsibilities': [],
        'keywords': []
    }
    
    # Extract skills
    skill_patterns = [
        r'\b(?:Python|Java|JavaScript|React|Angular|Vue|Node\.js|Django|Flask|Spring|SQL|MongoDB|PostgreSQL|MySQL|AWS|Azure|GCP|Docker|Kubernetes|Git|CI/CD|REST|API|HTML|CSS|TypeScript|C\+\+|C#|Ruby|PHP|Go|Rust|Scala|Machine Learning|AI|Data Science|Analytics|Tableau|Power BI|Excel|Leadership|Management|Communication|Problem Solving|Agile|Scrum|DevOps|Testing|QA|UX|UI|Product Management|Project Management|Marketing|Sales|Customer Service|Finance|Accounting|HR|Operations|Strategy|Business Analysis|Data Analysis|Research|Writing|Design|Creative|Photoshop|Illustrator|Figma|Sketch)\b',
    ]
    
    for pattern in skill_patterns:
        matches = re.findall(pattern, job_description, re.IGNORECASE)
        requirements['skills'].extend(matches)
    
    # Extract experience requirements
    exp_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', job_description, re.IGNORECASE)
    if exp_match:
        requirements['experience_years'] = exp_match.group(1)
    
    # Extract education requirements
    edu_match = re.search(r'(bachelor|master|phd|degree|diploma)', job_description, re.IGNORECASE)
    if edu_match:
        requirements['education'] = edu_match.group(1)
    
    # Extract key responsibilities
    lines = job_description.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('•') or line.startswith('-') or line.startswith('*'):
            requirements['key_responsibilities'].append(line[1:].strip())
    
    # Extract all keywords
    words = re.findall(r'\b[A-Za-z]{3,}\b', job_description)
    requirements['keywords'] = list(set(words))
    
    return requirements

def generate_tailored_resume(resume_sections, job_requirements):
    """Generate a tailored resume based on job requirements"""
    
    # Extract name from contact info or use placeholder
    name = "John Doe"
    contact_info = resume_sections.get('contact', '')
    
    # Try to extract name from first few lines
    if resume_sections.get('other'):
        first_lines = resume_sections['other'][:3]
        for line in first_lines:
            if len(line.split()) <= 3 and any(c.isupper() for c in line):
                name = line
                break
    
    # Build tailored resume
    tailored_resume = f"""
    <div class="resume-header">
        <div class="resume-name">{name}</div>
        <div class="resume-contact">{contact_info or 'Email: john.doe@email.com | Phone: (555) 123-4567 | LinkedIn: linkedin.com/in/johndoe'}</div>
    </div>
    
    <div class="resume-section">
        <div class="section-title">Professional Summary</div>
        <p>Results-driven professional with {job_requirements.get('experience_years', '5+')} years of experience in {', '.join(job_requirements['skills'][:3]) if job_requirements['skills'] else 'relevant technologies'}. Proven track record of delivering high-quality solutions and driving business success. Skilled in {', '.join(job_requirements['skills'][:5]) if job_requirements['skills'] else 'various technologies'} with a strong focus on {job_requirements['key_responsibilities'][0] if job_requirements['key_responsibilities'] else 'achieving results'}.</p>
    </div>
    
    <div class="resume-section">
        <div class="section-title">Core Competencies</div>
        <div class="skills-list">
            {generate_skills_html(job_requirements['skills'], resume_sections.get('skills', []))}
        </div>
    </div>
    
    <div class="resume-section">
        <div class="section-title">Professional Experience</div>
        {generate_experience_html(resume_sections.get('experience', []), job_requirements)}
    </div>
    
    <div class="resume-section">
        <div class="section-title">Education</div>
        {generate_education_html(resume_sections.get('education', []), job_requirements)}
    </div>
    """
    
    return tailored_resume

def generate_skills_html(job_skills, resume_skills):
    """Generate skills HTML based on job requirements"""
    # Combine and prioritize skills
    all_skills = job_skills[:15]  # Top 15 job skills
    
    # Add relevant skills from resume
    resume_skills_text = ' '.join(resume_skills).lower()
    for skill in job_skills:
        if skill.lower() in resume_skills_text:
            all_skills.append(skill)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_skills = []
    for skill in all_skills:
        if skill.lower() not in seen:
            seen.add(skill.lower())
            unique_skills.append(skill)
    
    return ''.join([f'<span class="skill-item">{skill}</span>' for skill in unique_skills[:20]])

def generate_experience_html(experience_lines, job_requirements):
    """Generate experience HTML tailored to job requirements"""
    if not experience_lines:
        # Create sample experience if none provided
        return f"""
        <div class="job-entry">
            <div class="job-title">Senior {job_requirements['skills'][0] if job_requirements['skills'] else 'Software'} Developer</div>
            <div class="job-company">ABC Company</div>
            <div class="job-date">2020 - Present</div>
            <div class="job-description">
                <ul>
                    <li>Developed and maintained applications using {', '.join(job_requirements['skills'][:3]) if job_requirements['skills'] else 'various technologies'}</li>
                    <li>Collaborated with cross-functional teams to deliver high-quality software solutions</li>
                    <li>Implemented best practices for code quality, testing, and deployment</li>
                    <li>Mentored junior developers and contributed to technical decision-making</li>
                </ul>
            </div>
        </div>
        """
    
    # Process existing experience
    experience_html = ""
    current_job = {}
    
    for line in experience_lines:
        if line and not line.startswith('•') and not line.startswith('-'):
            # This might be a job title/company
            if current_job:
                experience_html += format_job_entry(current_job, job_requirements)
            current_job = {'title': line, 'responsibilities': []}
        else:
            # This is a responsibility
            current_job['responsibilities'].append(line)
    
    if current_job:
        experience_html += format_job_entry(current_job, job_requirements)
    
    return experience_html

def format_job_entry(job, job_requirements):
    """Format individual job entry"""
    title = job.get('title', 'Software Developer')
    responsibilities = job.get('responsibilities', [])
    
    # Enhance responsibilities with job keywords
    enhanced_responsibilities = []
    for resp in responsibilities:
        # Add relevant keywords to responsibilities
        enhanced_resp = resp
        for skill in job_requirements['skills'][:5]:
            if skill.lower() not in resp.lower():
                enhanced_resp = enhanced_resp.replace('developed', f'developed using {skill}', 1)
        enhanced_responsibilities.append(enhanced_resp)
    
    return f"""
    <div class="job-entry">
        <div class="job-title">{title}</div>
        <div class="job-company">Previous Company</div>
        <div class="job-date">2018 - Present</div>
        <div class="job-description">
            <ul>
                {''.join([f'<li>{resp}</li>' for resp in enhanced_responsibilities[:4]])}
            </ul>
        </div>
    </div>
    """

def generate_education_html(education_lines, job_requirements):
    """Generate education HTML"""
    if not education_lines:
        degree = job_requirements.get('education', 'Bachelor')
        return f"""
        <div class="job-entry">
            <div class="job-title">{degree.title()}'s Degree in Computer Science</div>
            <div class="job-company">University Name</div>
            <div class="job-date">2014 - 2018</div>
        </div>
        """
    
    return f"""
    <div class="job-entry">
        <div class="job-title">{education_lines[0] if education_lines else "Bachelor's Degree"}</div>
        <div class="job-company">University Name</div>
        <div class="job-date">2014 - 2018</div>
    </div>
    """

@app.route('/generate', methods=['POST'])
def generate_resume():
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
        
        # Parse resume sections
        resume_sections = parse_resume_sections(resume_text)
        
        # Extract job requirements
        job_requirements = extract_job_requirements(job_description)
        
        # Generate tailored resume
        tailored_resume = generate_tailored_resume(resume_sections, job_requirements)
        
        return jsonify({'tailored_resume': tailored_resume})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
