import os
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
import openai
from openai import RateLimitError
from docx import Document
from werkzeug.utils import secure_filename

# Load env
openai.api_key = os.getenv("OPENAI_API_KEY")
UPLOAD = "uploads"
ALLOWED = {"docx", "txt"}

os.makedirs(UPLOAD, exist_ok=True)
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")

@app.errorhandler(RateLimitError)
def handle_rate_limit(err):
    flash("❌ OpenAI quota exceeded. Check billing or API key.")
    return redirect(url_for('index'))

@app.route('/', methods=['GET','POST'])
def index():
    if request.method=='POST':
        # validate
        resume = request.files.get('resume')
        jd     = request.files.get('jd')
        if not resume or not resume.filename.lower().endswith('.docx'):
            flash('Upload a .docx resume'); return redirect(url_for('index'))
        if not jd or not jd.filename.lower().endswith('.txt'):
            flash('Upload a .txt job description'); return redirect(url_for('index'))
        # save
        rfn = secure_filename(resume.filename)
        jfn = secure_filename(jd.filename)
        rpath = os.path.join(UPLOAD, rfn)
        jpath = os.path.join(UPLOAD, jfn)
        resume.save(rpath); jd.save(jpath)
        # extract
        resume_text = '\n'.join(p.text for p in Document(rpath).paragraphs)
        jd_text     = open(jpath,'r',encoding='utf-8').read()
        # prompt
        prompt = f"""
You are a professional resume writer. Given the resume paragraphs and the job description, rewrite only the bullet points under each section to:
- inject keywords from JD, use strong action verbs.
- preserve all headings, section breaks, and formatting.
Return new resume text, with paragraphs identical except bullets replaced.

RESUME:
{resume_text}

JD:
{jd_text}
"""
        resp = openai.chat.completions.create(
            model="gpt-4o", messages=[{"role":"user","content":prompt}],
            temperature=0.2, max_tokens=2000
        )
        new_text = resp.choices[0].message.content
        # build new doc
        doc = Document(rpath)
        # clear all bullets
        # collect new bullets by splitting new_text
        lines = new_text.splitlines()
        bullet_lines = [ln for ln in lines if ln.strip().startswith('- ')]
        # replace bullets in doc
        new_doc = Document()
        for para in doc.paragraphs:
            style = para.style.name
            if style.lower().startswith('list') and bullet_lines:
                txt = bullet_lines.pop(0)[2:].strip()
                new_doc.add_paragraph(txt, style=style)
            else:
                p = new_doc.add_paragraph()
                run = p.add_run(para.text)
                p.style = style
        # save
        out = os.path.join(UPLOAD, f"tailored_{rfn}")
        new_doc.save(out)
        return send_file(out, as_attachment=True,
                         download_name=f"tailored_{rfn}")
    return render_template('index.html')
