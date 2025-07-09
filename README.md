# Resume Tailor - AI-Powered Resume Optimization

An intelligent web application that automatically tailors resumes to specific job descriptions using AI, making them ATS-friendly and keyword-optimized.

## Features

- 📄 **Resume Upload**: Support for .docx format
- 📋 **Job Description Input**: Accept .txt job descriptions
- 🤖 **AI-Powered Tailoring**: Uses OpenAI GPT for intelligent optimization
- 🎯 **ATS Optimization**: Formats resumes for Applicant Tracking Systems
- 🔍 **Keyword Matching**: Automatically incorporates relevant keywords
- ⚡ **Instant Results**: Fast processing and download
- 📱 **Mobile-Friendly**: Responsive design for all devices

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/resume-tailor.git
cd resume-tailor
```

### 2. Set Up Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your credentials
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
```

### 4. Run the Application
```bash
python app.py
```

Visit `http://localhost:5000` to use the application.

## Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Set your environment variables
export OPENAI_API_KEY=your_api_key
export SECRET_KEY=your_secret_key

# Run with docker-compose
docker-compose up -d
```

### Using Docker
```bash
# Build image
docker build -t resume-tailor .

# Run container
docker run -p 5000:5000 \
  -e OPENAI_API_KEY=your_api_key \
  -e SECRET_KEY=your_secret_key \
  resume-tailor
```

## API Endpoints

- `GET /` - Main application interface
- `POST /upload` - Upload resume and job description
- `GET /download/<session_id>` - Download tailored resume
- `GET /health` - Health check endpoint

## How It Works

1. **Upload**: User uploads resume (.docx) and job description (.txt)
2. **Parse**: Application extracts text from both files
3. **Analyze**: AI analyzes job requirements and resume content
4. **Optimize**: AI tailors resume with:
   - Relevant keywords
   - ATS-friendly formatting
   - Optimized summary
   - Enhanced experience descriptions
5. **Download**: User receives optimized resume in .docx format

## Production Deployment

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: Flask secret key for sessions
- `PORT`: Port number (default: 5000)
- `DEBUG`: Set to "false" for production

### Deployment Platforms

#### Heroku
```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_key
heroku config:set SECRET_KEY=your_secret
git push heroku main
```

#### AWS/Google Cloud
Deploy using container services with the provided Dockerfile.

#### VPS/Server
```bash
# Install dependencies and run with gunicorn
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 app:app
```

## File Structure
```
resume-tailor/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── .env.example          # Environment variables example
├── .gitignore           # Git ignore rules
├── README.md            # This file
└── templates/
    └── index.html       # Web interface
```

## Security Considerations

- Files are temporarily stored and automatically deleted after processing
- No permanent storage of personal data
- Input validation and file type restrictions
- Rate limiting recommended for production use

## Cost Optimization

- Uses GPT-3.5-turbo for cost-effective processing
- Implements prompt optimization to reduce token usage
- Automatic cleanup of temporary files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open a GitHub issue or contact the maintainers.

---

**Note**: Make sure to keep your OpenAI API key secure and never commit it to version control.
