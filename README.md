# Resume Ranking System

A Python-based system that automatically scores and ranks resumes against a predefined job description using state-of-the-art AI techniques.

## Features

- **Multi-format Support**: Processes PDF and DOCX resume files
- **Intelligent OCR**: Uses Gemini 2.5 Flash for scanned/image-based PDFs
- **Structured Extraction**: Converts unstructured resume text to structured JSON
- **Smart Skill Matching**: LLM-based semantic matching (Flask → Python, EC2 → AWS)
- **Deterministic Scoring**: Same resume always produces same score
- **Ranked Output**: Displays candidates from best to worst match

---

## Setup Instructions

### Prerequisites
- Python 3.8+
- Gemini API Key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/jaibhasin/resume-ranker.git
cd resume-ranker
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API Key**
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_api_key_here
```

---

## Usage

### Process resumes from a folder
```bash
python main.py --folder ./resumes/
```

### Process specific resume files
```bash
python main.py --files resume1.pdf resume2.docx resume3.pdf
```

### Rules
- Maximum 10 resumes processed per run
- Supported formats: PDF, DOCX
- Invalid/unreadable files are skipped gracefully

---

## Scoring Logic

### Overview
The system uses a **weighted scoring algorithm** with four components:

| Component | Weight | Description |
|-----------|--------|-------------|
| **Skills Match** | 40% | Technical skills alignment with job requirements |
| **Experience** | 30% | Years of relevant experience |
| **Role Relevance** | 20% | Job title alignment with target role |
| **Education** | 10% | Academic background relevance |

**Total Score Range**: 0-100

---

### 1. Skills Matching (40 points)

**Method**: LLM-based semantic matching using Gemini 2.5 Flash

**How it works**:
- Candidate skills are compared against required skills using AI
- Handles semantic equivalence (e.g., "Flask" satisfies "Python", "EC2" satisfies "AWS")
- Temperature=0 ensures deterministic results

**Formula**:
```
Skills Score = (Matched Skills / Required Skills) × 100
Weighted Score = Skills Score × 0.40
```

**Example**:
- Required: `[python, javascript, react, aws, docker, git, sql, nodejs, rest apis]` (9 skills)
- Candidate has: `[Flask, Django, TypeScript, EC2, GitHub, PostgreSQL]`
- LLM matches: `[python, javascript, aws, git, sql]` (5 skills)
- Score: (5/9) × 100 = 55.56
- Weighted: 55.56 × 0.40 = **22.22 points**

---

### 2. Experience Scoring (30 points)

**Method**: Mathematical formula based on years of experience

**Formula**:
```python
if years < required:
    score = (years / required) × 100  # Proportional penalty
else:
    score = 100  # Full score if meets requirement
    
Weighted Score = score × 0.30
```

**Example**:
- Required: 3+ years
- Candidate: 4 years
- Score: 100
- Weighted: 100 × 0.30 = **30 points**

---

### 3. Role Relevance (20 points)

**Method**: Keyword matching in job titles

**How it works**:
- Analyzes all job titles in work history
- Counts roles containing software engineering keywords
- Keywords: `software, developer, engineer, programmer, full-stack, backend, frontend, devops, architect`

**Formula**:
```
Relevance Score = (Relevant Roles / Total Roles) × 100
Weighted Score = Relevance Score × 0.20
```

**Example**:
- Total roles: 5
- Relevant roles: 4 (e.g., "Software Engineer", "Full-Stack Developer")
- Score: (4/5) × 100 = 80
- Weighted: 80 × 0.20 = **16 points**

---

### 4. Education Scoring (10 points)

**Method**: Tiered scoring based on degree relevance

**Tiers**:
- **Tier 1 (100 pts)**: Computer Science, Software Engineering
- **Tier 2 (80 pts)**: Information Technology, Data Science, Electrical Engineering
- **Tier 3 (60 pts)**: Other Engineering/Science degrees
- **Tier 4 (40 pts)**: Any Bachelor's/Master's degree
- **No degree (30 pts)**: Experience-based candidate

**Formula**:
```
Weighted Score = Tier Score × 0.10
```

**Example**:
- Degree: "BS Computer Science"
- Tier: 1 (100 points)
- Weighted: 100 × 0.10 = **10 points**

---

### Final Score Calculation

```
Total Score = Skills (40%) + Experience (30%) + Relevance (20%) + Education (10%)
```

**Example**:
```
Skills:     22.22 points
Experience: 30.00 points
Relevance:  16.00 points
Education:  10.00 points
─────────────────────────
Total:      78.22 / 100
```

---

## Determinism Guarantee

The system ensures **100% reproducible scores**:

1. **LLM Calls**: `temperature=0` (no randomness)
2. **Structured Output**: JSON schema enforced via Pydantic
3. **Skill Matching**: LLM forced to return exact skill names from required list
4. **Mathematical Scoring**: Pure Python calculations (no randomness)
5. **File Ordering**: Sorted alphabetically for consistent processing

**Result**: Same resume + same job description = **same score every time**

---

## Architecture

```
main.py
   ↓
parser.py (Text Extraction)
   ├── pdfplumber (text-based PDFs)
   ├── python-docx (DOCX files)
   └── Gemini 2.5 Flash OCR (scanned PDFs)
   ↓
extractor.py (Structured Data)
   └── Gemini 2.5 Flash (JSON extraction)
   ↓
scorer.py (Scoring)
   ├── LLM skill matching
   └── Rule-based calculations
   ↓
Ranked Output
```

---

## Libraries Used

| Library | Purpose | Why Chosen |
|---------|---------|------------|
| **google-generativeai** | Gemini API access | SOTA LLM for extraction & matching |
| **pdfplumber** | PDF text extraction | Best for complex layouts |
| **python-docx** | DOCX parsing | Standard for Word documents |
| **pydantic** | Data validation | Ensures structured output |
| **python-dotenv** | Environment variables | Secure API key management |
| **numpy** | (Optional) Math operations | Potential future use |

---

## AI Tools Used

### 1. **Gemini 2.5 Flash** (Primary LLM)

**Used for**:
- OCR on scanned/image-based PDFs
- Structured data extraction from resume text
- Semantic skill matching

**Why**:
- Fast inference (Flash variant)
- Native structured output (JSON mode)
- Multimodal capabilities (handles images)
- Cost-effective compared to GPT-4

**Configuration**:
- `temperature=0` for determinism
- Pydantic schema enforcement
- Response validation

### 2. **Development Tools**
- GitHub Copilot: Code suggestions
- ChatGPT: Architecture discussions

---

## Assumptions

1. **Resume Quality**: Assumes resumes are in English and reasonably formatted
2. **Skill Naming**: LLM handles variations (React.js vs react vs ReactJS)
3. **Experience Calculation**: Total years summed from all roles
4. **File Limit**: Maximum 10 resumes to balance processing time and API costs
5. **API Availability**: Requires active internet connection for Gemini API

---

## Output Format

```
================================================================================
FINAL RANKINGS
================================================================================

1. resume_5.docx – Score: 87.11
   Candidate: Dennis Schröder
   Skills: 7/9 matched. 14.0y (meets 3+ req). 7/7 relevant.
   Breakdown: Skills=77.8 | Experience=100.0 | Relevance=100.0 | Education=60.0
   ✓ Matched skills: aws, docker, git, javascript, python, react, sql
   ✗ Missing skills: nodejs, rest apis

2. resume_2.pdf – Score: 84.56
   ...
```

Results are also saved to `ranking_results.json` for programmatic access.

---

## Project Structure

```
resume-ranker/
├── main.py              # Entry point & orchestration
├── parser.py            # Text extraction (PDF/DOCX/OCR)
├── extractor.py         # Structured data extraction
├── scorer.py            # Scoring logic
├── job_constants.py     # Hardcoded job description
├── requirements.txt     # Dependencies
├── .env                 # API keys (not in repo)
├── .gitignore          # Git ignore rules
├── README.md           # This file
└── resumes/            # Sample resumes (not in repo)
```

---

## Future Enhancements

- [ ] Batch processing with async API calls
- [ ] Configurable weights for scoring components
- [ ] Multiple job description support
- [ ] Export to CSV/Excel
- [ ] Web UI for non-technical users

---

## License

MIT License - Feel free to use and modify

---

## Author

Jai Bhasin  
GitHub: [@jaibhasin](https://github.com/jaibhasin)