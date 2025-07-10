# Resume Tailor (No API Key)

A Flask app that uses a local Hugging Face model to tailor your `.docx` resume for any job `.txt` description—no external API key needed.

## Setup & Deploy (Render)
1. Push this repo to GitHub.
2. In Render, create a new **Web Service** from your GitHub repo.
3. **Environment**: set `FLASK_SECRET_KEY` to any random string.
4. **Build**: Render will detect the Dockerfile and build automatically.
5. **Deploy**: Once up, your service URL will be live.

## Local Testing (Docker)
```bash
docker build -t resume-tailor .
docker run -p 5000:5000 resume-tailor
