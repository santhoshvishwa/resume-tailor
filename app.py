import os
from flask import Flask, request, render_template, send_file, redirect, url_for, flash
import openai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from docx import Document
from werkzeug.utils import secure_filename
from pyngrok import ngrok

# ─── CONFIG ─────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
if token := os.getenv("NGROK_AUTH_TOKEN"):
    ngrok.set_auth_token(token)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTS  = {"pdf", "docx", "txt"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(fname):
    return "." in fname and fname.rsplit(".",1)[1].lower() in ALLOWED_EXTS


def extract_text(path):
    ext = path.rsplit(".",1)[1].lower()
    if ext == "docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    with open(path, "r", errors="ignore") as f:
        return f.read()


# ─── STEP 1: LazyApply job search ───────────────────────────────────────────
def lazyapply_search(email, password, keywords):
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.get("https://app.lazyapply.com/login")
    # —— TODO: fill in your login & search logic —— #
    # driver.find_element(...).send_keys(email)
    # driver.find_element(...).send_keys(password)
    # driver.find_element(...).click()
    # driver.get(f"https://app.lazyapply.com/jobs?search={keywords}")
    jobs = []
    # for e in driver.find_elements(...):
    #     jobs.append({ ... })
    driver.quit()
    return jobs


def get_job_description(job_url):
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.get(job_url)
    jd = driver.find_element("css selector","div.job-description").text
    driver.quit()
    return jd


# ─── STEP 2: Jobalytics‐style analysis + bullet generation ────────────────
def find_missing_keywords(resume_text, jd_text):
    prompt = (
        "You are an ATS optimization assistant.\n\n"
        "Resume:\n" + resume_text + "\n\n"
        "Job Description:\n" + jd_text + "\n\n"
        "List, comma-separated, the keywords in the JD that are missing from the resume."
    )
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"user","content":prompt}],
        temperature=0.0,
        max_tokens=200
    )
    return [k.strip() for k in resp.choices[0].message.content.split(",") if k.strip()]


def generate_bullet(missing):
    kws = ", ".join(missing)
    prompt = f"Write one concise, impact-oriented resume bullet that uses these keywords: {kws}."
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2,
        max_tokens=60
    )
    return resp.choices[0].message.content.strip()


# ─── STEP 3: Tailor & Submit ───────────────────────────────────────────────
def tailor_resume(resume_text, jd_text):
    prompt = (
        "You are a resume optimization assistant.\n\n"
        "Resume:\n" + resume_text + "\n\n"
        "Job Description:\n" + jd_text + "\n\n"
        "Generate a concise, tailored resume highlighting only the skills, tools, "
        "and achievements most relevant to the JD."
    )
    resp = openai.chat.completions.create(
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
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    wait = WebDriverWait(driver, 15)
    driver.get(app_url)

    if "linkedin.com/jobs" in app_url:
        ea = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
            "button[data-control-name*='easy_apply']")))
        ea.click()
        up = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
            "input[type='file']")))
        up.send_keys(os.path.abspath(filepath))
        while True:
            try:
                submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                    "button[aria-label='Submit application'],button[data-control-name='submit_unify']")))
                submit_btn.click()
                break
            except:
                nxt = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                    "button[aria-label='Continue to next step'],button[aria-label='Next']")))
                nxt.click()
    else:
        fld = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
            "input[type='file']")))
        fld.send_keys(os.path.abspath(filepath))
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
            "button[type='submit']")))
        btn.click()

    driver.quit()


# ─── ROUTES ────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        email    = request.form["email"]
        password = request.form["password"]
        search   = request.form["search"]
        resume   = request.files.get("resume")
        if not (resume and allowed_file(resume.filename)):
            flash("❌ Valid resume file required (.docx/.txt).")
            return redirect(url_for("index"))
        fn   = secure_filename(resume.filename)
        path = os.path.join(UPLOAD_FOLDER, fn)
        resume.save(path)
        jobs = lazyapply_search(email, password, search)
        return render_template("results.html", jobs=jobs, resume_fn=fn)
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    job_url   = request.form["job_url"]
    resume_fn = request.form["resume_fn"]
    rpath     = os.path.join(UPLOAD_FOLDER, resume_fn)
    resume_txt = extract_text(rpath)
    jd_txt     = get_job_description(job_url)
    missing    = find_missing_keywords(resume_txt, jd_txt)
    bullet     = generate_bullet(missing)
    tailored   = tailor_resume(resume_txt, jd_txt) + "\n\n• " + bullet
    out_fn     = "tailored_" + resume_fn
    out_path   = os.path.join(UPLOAD_FOLDER, out_fn)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(tailored)
    return render_template("analyzed.html",
                           new_resume=out_fn,
                           job_url=job_url,
                           missing=missing,
                           bullet=bullet)

@app.route("/apply", methods=["POST"])
def apply():
    new_fn  = request.form["new_resume"]
    job_url = request.form["job_url"]
    automate_submission(job_url, os.path.join(UPLOAD_FOLDER, new_fn))
    return render_template("done.html")

if __name__ == "__main__":
    public_url = ngrok.connect(5000)
    print(" * Public URL:", public_url)
    app.run(port=5000)
