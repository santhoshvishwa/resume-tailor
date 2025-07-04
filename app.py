import os
from flask import Flask, request, render_template, send_file
import openai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from werkzeug.utils import secure_filename
from pyngrok import ngrok

# ─── CONFIG ─────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
NGROK_TOKEN    = os.getenv("NGROK_AUTH_TOKEN", None)
if NGROK_TOKEN:
    ngrok.set_auth_token(NGROK_TOKEN)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTS  = {"pdf", "docx", "txt"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(fname):
    return "." in fname and fname.rsplit(".",1)[1].lower() in ALLOWED_EXTS

def tailor_resume(resume_text, jd_text):
    prompt = (
        "You are a resume optimization assistant.\n\n"
        "Resume:\n" + resume_text + "\n\n"
        "Job Description:\n" + jd_text + "\n\n"
        "Generate a concise, tailored resume highlighting only the skills, tools, "
        "and achievements most relevant to the JD."
    )
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2,
        max_tokens=1500
    )
    return resp.choices[0].message.content

def automate_submission(app_url, filepath):
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)
    driver.get(app_url)
    driver.find_element("css selector", "input[type='file']").send_keys(os.path.abspath(filepath))
    driver.find_element("css selector", "button[type='submit']").click()
    driver.quit()

@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        # handle resume upload
        resume = request.files.get("resume")
        jd_text = request.form.get("jd_text", "").strip()
        app_url = request.form.get("app_url", "").strip()

        if not (resume and allowed_file(resume.filename)):
            return "❌ Invalid resume file type", 400
        if not jd_text:
            return "❌ Job description is required", 400

        # save resume
        rfn   = secure_filename(resume.filename)
        rpath = os.path.join(app.config["UPLOAD_FOLDER"], rfn)
        resume.save(rpath)

        # read resume text
        with open(rpath, "r", errors="ignore") as f:
            resume_text = f.read()

        # tailor
        tailored = tailor_resume(resume_text, jd_text)

        # write out tailored version
        tfname = "tailored_resume.txt"
        tpath  = os.path.join(app.config["UPLOAD_FOLDER"], tfname)
        with open(tpath, "w", encoding="utf-8") as f:
            f.write(tailored)

        return render_template("result.html",
                               tailored_file=tfname,
                               app_url=app_url)

    return render_template("index.html")

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(app.config["UPLOAD_FOLDER"], filename),
                     as_attachment=True)

@app.route("/submit", methods=["POST"])
def submit():
    tf      = request.form["tailored_file"]
    app_url = request.form["app_url"]
    filepath= os.path.join(app.config["UPLOAD_FOLDER"], tf)
    automate_submission(app_url, filepath)
    return "✅ Resume submitted successfully!"

if __name__ == "__main__":
    public_url = ngrok.connect(5000)
    print(f" * Public URL: {public_url}")
    app.run(port=5000)
