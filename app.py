import os
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
import openai
from docx import Document
from werkzeug.utils import secure_filename
from io import BytesIO

# ─── CONFIG ─────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")

ALLOWED_DOCX = {"docx"}
ALLOWED_TXT  = {"txt"}
UPLOAD       = "uploads"
os.makedirs(UPLOAD, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this")

def allowed(filename, exts):
    return "." in filename and filename.rsplit(".",1)[1].lower() in exts

def extract_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

# ─── ROUTES ──────────────────────────────────────────

@app.route("/", methods=["GET","POST"])
def home():
    if request.method=="POST":
        # 1) Validate uploads
        resume = request.files.get("resume")
        jd     = request.files.get("jd")
        if not (resume and allowed(resume.filename, ALLOWED_DOCX)):
            flash("Please upload a .docx resume."); return redirect(url_for("home"))
        if not (jd and allowed(jd.filename, ALLOWED_TXT)):
            flash("Please upload a .txt job description."); return redirect(url_for("home"))

        # 2) Save to disk
        rfn = secure_filename(resume.filename)
        jfn = secure_filename(jd.filename)
        rpath = os.path.join(UPLOAD, rfn)
        jpath = os.path.join(UPLOAD, jfn)
        resume.save(rpath); jd.save(jpath)

        # 3) Extract text
        resume_text = extract_docx(rpath)
        jd_text     = open(jpath, "r", encoding="utf-8").read()

        # 4) Build prompt & call OpenAI
        prompt = f"""
You are a professional resume writer.  Given this Resume:
{resume_text}

And this Job Description:
{jd_text}

Rewrite the resume to be ATS-friendly for this JD. 
– Add keywords from the JD. 
– Rewrite the summary to match role. 
– Highlight matching skills & experience.
– Use strong action verbs and bullet points.
Return only the new resume text.
"""
        resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"user","content":prompt}],
            temperature=0.2,
            max_tokens=2000
        )
        new_text = resp.choices[0].message.content.strip()

        # 5) Write out a new .docx
        out_doc = Document()
        for line in new_text.split("\n"):
            if line.startswith("- ") or line.startswith("• "):
                out_doc.add_paragraph(line[2:], style="List Bullet")
            else:
                out_doc.add_paragraph(line)
        bio = BytesIO()
        out_doc.save(bio)
        bio.seek(0)

        # 6) Send as download
        return send_file(
            bio,
            as_attachment=True,
            download_name="Tailored_"+rfn,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    return render_template("index.html")
