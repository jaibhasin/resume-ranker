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

## Explanation of the scoring logic
For scoring we are using 4 components with weights:
1. Skills (45%) : instead of using hard-coded matching , we are using SOTA way of matching skills using LLM (e.g. js, javascript, nodejs also are related by couldnt be understood by embeddings, and hardcoding would have it's own limitations)
2. Experience (30%) : here we are jusitng simply checking if the candidate has the required experience
3. Relevance (15%) : using gemini to measaure how relevent are the past jobs to the current role
4. Education (10%) : here also we are using LLM to check if the education is relevent to the role or not

(currently we are using 3 api calls for scoring in all, we should reduced later. Either by using a smaller llm or by combining api calls to one)

We have made the scoring Deterministic, so the resume gets same score everytime.

I have given accuracy a higher priority over speed while designing the system


## Libraries used and reasons for choosing them
pdfplumber : used for extracting text from pdfs (handles all formats along with tables,multi-column text)

python-docx	: used for extracting text from docx files (this is industry standard)

pydantic : this is used to force the LLM to give the output in the exact json format which is required later for scoring

google-generativeai : used to access gemini-api (can be later changed with claude/openai)

## Any assumptions made

1) We are assuming resumes are in pdf or docx format and in english (pdf can contain both text and images)
2) Total Experience is calculated by adding all the years of experience in past jobs
3) API available 


## All AI tools used and how
This is the final determistic resume scoring system I built.

I used resumes from reddit for testing.  
IDE used was Google's Antigravity  
I am using gemini-2.5-flash api for processing (could have use gemini-3.0)

I tried to understand the best approach for implementing this, for which I took help of chatgpt, claude and gemini, to understand all kinds of approaches. 

I designed the full software architecture, and implemented each file step by step. (used Antigravity side by side)
I implmented in the following order : main.py , parser.py , extract.py , scorer.py

For each call made to gemini, its prompt was written by Antigravity (under my supervision)

Used Antigravity for testing and debugging

Process : 
1. get resumes from user using CLI
2. extract all the text from resume 
3. We have unstructred data now, which we need to get in structured format. We use gemini(temp=0) to get data in json format using pydantic schema
4. Then apply the scoring logic to get score for each resume
