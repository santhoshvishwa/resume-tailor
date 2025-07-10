import os
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from docx import Document
from werkzeug.utils import secure_filename
from transformers import pipeline

# ─── CONFIG ─────────────────────────────────────────────────────────────
UPLOAD_FOLDER = "uploads"
ALLOWED = {"docx", "txt"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")

# load a local text2text model (small enough for free tier CPU)
generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    device=-1  # CPU inference
)

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        resume_file = request.files.get('resume')
        jd_file     = request.files.get('jd')
        if not resume_file or not resume_file.filename.lower().endswith('.docx'):
            flash('Please upload a .docx resume')
            return redirect(url_for('index'))
        if not jd_file or not jd_file.filename.lower().endswith('.txt'):
            flash('Please upload a .txt job description')
            return redirect(url_for('index'))

        # save uploads
        rfn = secure_filename(resume_file.filename)
        jfn = secure_filename(jd_file.filename)
        rpath = os.path.join(UPLOAD_FOLDER, rfn)
        jpath = os.path.join(UPLOAD_FOLDER, jfn)
        resume_file.save(rpath)
        jd_file.save(jpath)

        # extract text
        resume_text = '\n'.join(p.text for p in Document(rpath).paragraphs)
        jd_text     = open(jpath, 'r', encoding='utf-8').read()

        # prompt for rewriting bullets only
        prompt = (
            "Rewrite only the bullet points in this resume to be ATS-friendly for the job description, "
            "injecting keywords from the JD and using strong action verbs. "
            "Preserve all headings, spacing, and non-bullet content intact.\n\n"
            "Resume:\n" + resume_text + "\n\n"
            "Job Description:\n" + jd_text
        )

        # run through transformer model
        out = generator(prompt, max_length=1500, num_return_sequences=1)[0]['generated_text']

        # rebuild .docx preserving non-bullets
        original = Document(rpath)
        new_doc = Document()
        bullets = [ln[2:].strip() for ln in out.splitlines() if ln.strip().startswith('- ')]
        for para in original.paragraphs:
            style = para.style.name
            if style.lower().startswith('list') and bullets:
                new_doc.add_paragraph(bullets.pop(0), style=style)
            else:
                p = new_doc.add_paragraph()
                p.style = style
                p.add_run(para.text)

        out_path = os.path.join(UPLOAD_FOLDER, f"tailored_{rfn}")
        new_doc.save(out_path)

        return send_file(
            out_path,
            as_attachment=True,
            download_name=f"tailored_{rfn}" 
        )

    return render_template('index.html')
