# Resume Ranking System

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
Create a `.env` file in the project root:
```bash
touch .env
```

Add your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

### 3. Prepare Job Description
Edit `job_constants.py` to define your job requirements:
```python
JOB_DESCRIPTION = {
    "title": "Software Engineer",
    "description": "Job description here...",
    "required_skills": ['python', 'javascript', 'react', ...],
    "required_experience": 3,
    "job_summary": "Brief summary..."
}
```

## Execution

### Option 1: Process resumes from a folder
```bash
python3 main.py --folder ./resumes/
```

### Option 2: Process specific files
```bash
python3 main.py --files resume1.pdf resume2.docx resume3.pdf
```
