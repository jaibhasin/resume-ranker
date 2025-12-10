"""
Resume Scorer: Deterministic scoring using LLM-based skill matching.
Uses Gemini 2.5 Flash with temperature=0 and strict enum output.
"""

import os
import json
from typing import Dict, List, Any, Tuple
import google.generativeai as genai
from dotenv import load_dotenv

# Load env and configure Gemini (only once)
load_dotenv()
_gemini_configured = False

def ensure_gemini_configured():
    """Configure Gemini API only if not already configured."""
    global _gemini_configured
    if not _gemini_configured:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        _gemini_configured = True


def match_skills_with_llm(candidate_skills: List[str], required_skills: List[str]) -> Tuple[List[str], str]:

    if not candidate_skills or not required_skills:
        return [], "No skills to match"
    
    ensure_gemini_configured()
    
    try:
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config=genai.GenerationConfig(
                temperature=0,
                response_mime_type="application/json",
            )
        )
        
        # Format required skills as explicit enum
        required_skills_lower = [s.lower() for s in required_skills]
        skills_enum = ", ".join([f'"{s}"' for s in required_skills_lower])
        
        prompt = f"""You are a skill matching system. Analyze candidate skills and return which required skills they satisfy.

REQUIRED SKILLS (you can ONLY return skills from this exact list):
{json.dumps(required_skills_lower)}

CANDIDATE'S SKILLS:
{json.dumps(candidate_skills)}

Rules:
1. You can ONLY return skills that exist EXACTLY in the REQUIRED SKILLS list above
2. A candidate skill satisfies a required skill if it's the same OR a related framework/tool:
   - "Flask", "Django" → satisfies "python"
   - "React Native", "TypeScript" → satisfies "javascript"  
   - "PostgreSQL", "MySQL" → satisfies "sql"
   - "EC2", "S3", "Lambda" → satisfies "aws"
   - "GitHub", "GitLab" → satisfies "git"
3. Be strict but fair

Return JSON in this EXACT format:
{{
  "matched_skills": ["skill1", "skill2"],
  "reasoning": "brief explanation"
}}

IMPORTANT: matched_skills array must ONLY contain values from this list: [{skills_enum}]"""

        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        # Strict validation: only keep skills that exactly match required skills
        matched_raw = result.get('matched_skills', [])
        matched = [s for s in matched_raw if s.lower() in required_skills_lower]
        reasoning = result.get('reasoning', '')
        
        return matched, reasoning
        
    except Exception as e:
        print(f"Error in LLM skill matching: {e}")
        # Fallback to exact matching
        candidate_lower = {s.lower() for s in candidate_skills}
        required_lower = set(required_skills_lower)
        return list(candidate_lower.intersection(required_lower)), "Fallback: exact match"


class ResumeScorer:
    """Deterministic resume scoring with LLM-based skill matching."""
    
    def __init__(self, job_description: Dict[str, Any]):
        self.jd = job_description
        self.job_title = job_description.get('title', '').lower()
        self.required_experience = job_description.get('required_experience', 0)
        self.required_skills = [s.lower() for s in job_description.get('required_skills', [])]
        
        self.weights = {
            'skills': 45,
            'experience': 30,
            'relevance': 15,
            'education': 10
        }
    
    def calculate_skills_score(self, candidate_skills: List[str]) -> Tuple[float, List[str], List[str], str]:
        """Calculate skills score using LLM matching with strict validation."""
        if not self.required_skills:
            return 100.0, [], [], "No skills required"
        
        if not candidate_skills:
            return 0.0, [], self.required_skills.copy(), "No skills provided"
        
        matched, reasoning = match_skills_with_llm(candidate_skills, self.required_skills)
        missing = [s for s in self.required_skills if s not in matched]
        
        score = (len(matched) / len(self.required_skills)) * 100
        return score, matched, missing, reasoning
    
    def calculate_experience_score(self, years: float) -> Tuple[float, str]:
        """Calculate experience score."""
        req = self.required_experience
        
        if req == 0:
            return 100.0, "No experience requirement"
        if years <= 0:
            return 0.0, "No experience listed"
        
        if years < req:
            return (years / req) * 100, f"{years:.1f}y (need {req}+)"
        return 100.0, f"{years:.1f}y (meets {req}+ req)"
    
    def calculate_relevance_score(self, experience: List[Dict]) -> Tuple[float, str]:
        """Calculate role relevance using LLM evaluation."""
        if not experience:
            return 0.0, "No work history"
        
        ensure_gemini_configured()
        
        try:
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                generation_config=genai.GenerationConfig(
                    temperature=0,
                    response_mime_type="application/json",
                )
            )
            
            job_titles = [exp.get('job_title', 'Unknown') for exp in experience]
            
            prompt = f"""You are a job relevance evaluator.

TARGET JOB: {self.jd.get('title', 'Unknown')}
JOB DESCRIPTION: {self.jd.get('description', 'Not provided')}

CANDIDATE'S PAST JOB TITLES:
{json.dumps(job_titles)}

Evaluate how relevant the candidate's work history is to the target job.

Scoring guidelines:
- 100: All roles directly relevant (e.g., all "Software Engineer" for Software Engineer role)
- 80: Most roles relevant (e.g., 4/5 relevant)
- 60: Some relevant experience (e.g., 2/5 relevant)
- 40: Minimal relevant experience (e.g., 1/5 relevant)
- 0: No relevant experience

Return JSON in this EXACT format:
{{
  "score": 80,
  "reasoning": "brief explanation"
}}

IMPORTANT: Score must be 0, 40, 60, 80, or 100"""

            response = model.generate_content(prompt)
            result = json.loads(response.text)
            
            score = result.get('score', 0)
            reasoning = result.get('reasoning', 'LLM evaluation')
            
            # Validate score
            if score not in [0, 40, 60, 80, 100]:
                score = 0
            
            return float(score), reasoning
            
        except Exception as e:
            print(f"Error in LLM relevance scoring: {e}")
            # Fallback to keyword matching
            keywords = {'software', 'developer', 'engineer', 'programmer', 'full-stack',
                       'fullstack', 'backend', 'frontend', 'web', 'devops', 'architect'}
            relevant = sum(1 for exp in experience 
                          if any(kw in exp.get('job_title', '').lower() for kw in keywords))
            total = len(experience)
            return (relevant / total) * 100 if total else 0, f"{relevant}/{total} relevant (fallback)"
    
    def calculate_education_score(self, education: List[Dict]) -> Tuple[float, str]:
        """Calculate education score using LLM-based relevance evaluation."""
        if not education:
            return 30.0, "No education listed"
        
        ensure_gemini_configured()
        
        try:
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                generation_config=genai.GenerationConfig(
                    temperature=0,
                    response_mime_type="application/json",
                )
            )
            
            # Format education for prompt
            education_list = [
                f"{edu.get('degree', 'Unknown')} from {edu.get('institution', 'Unknown')}"
                for edu in education
            ]
            
            prompt = f"""You are an education relevance evaluator for job applications.

JOB ROLE: {self.jd.get('title', 'Unknown')}
JOB DESCRIPTION: {self.jd.get('description', 'Not provided')}

CANDIDATE'S EDUCATION:
{json.dumps(education_list)}

Evaluate how relevant the candidate's education is to this specific job role.

Scoring guidelines:
- 100: Perfect match (e.g., CS degree for Software Engineer, MBA for Business Analyst)
- 80: Closely related field (e.g., IT/Data Science for Software Engineer)
- 60: Somewhat relevant technical/analytical background
- 40: Has a degree but not directly relevant
- 30: No education listed

Return JSON in this EXACT format:
{{
  "score": 100,
  "reasoning": "brief explanation of why this score"
}}

IMPORTANT: 
- Score must be one of: 100, 80, 60, 40, or 30
- Be consistent: same education + same job = same score every time"""

            response = model.generate_content(prompt)
            result = json.loads(response.text)
            
            score = result.get('score', 40)
            reasoning = result.get('reasoning', 'LLM evaluation')
            
            # Validate score is one of allowed values
            if score not in [100, 80, 60, 40, 30]:
                score = 40  # Default fallback
            
            return float(score), reasoning
            
        except Exception as e:
            print(f"Error in LLM education scoring: {e}")
            # Fallback to simple check
            for edu in education:
                degree = edu.get('degree', '').lower()
                if any(t in degree for t in ['computer science', 'software engineering']):
                    return 100.0, "CS/SE degree (fallback)"
                if any(t in degree for t in ['information technology', 'data science']):
                    return 80.0, "Related degree (fallback)"
            return 40.0, "Other degree (fallback)"
    
    def score(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total weighted score."""
        skills = resume_data.get('skills', [])
        years = resume_data.get('total_years_experience', 0)
        experience = resume_data.get('experience', [])
        education = resume_data.get('education', [])
        name = resume_data.get('name', 'Unknown')
        
        skills_score, matched, missing, reasoning = self.calculate_skills_score(skills)
        exp_score, exp_note = self.calculate_experience_score(years)
        rel_score, rel_note = self.calculate_relevance_score(experience)
        edu_score, edu_note = self.calculate_education_score(education)
        
        total = (
            (skills_score * self.weights['skills'] / 100) +
            (exp_score * self.weights['experience'] / 100) +
            (rel_score * self.weights['relevance'] / 100) +
            (edu_score * self.weights['education'] / 100)
        )
        
        explanation = f"Skills: {len(matched)}/{len(self.required_skills)} matched. {exp_note}. {rel_note}."
        
        return {
            "candidate_name": name,
            "total_score": round(total, 2),
            "explanation": explanation,
            "breakdown": {
                "skills": {"score": round(skills_score, 2), "weight": 40},
                "experience": {"score": round(exp_score, 2), "weight": 30},
                "relevance": {"score": round(rel_score, 2), "weight": 20},
                "education": {"score": round(edu_score, 2), "weight": 10}
            },
            "details": {
                "matched_skills": matched,
                "missing_skills": missing,
                "skill_reasoning": reasoning,
                "experience_years": years,
                "education_note": edu_note
            }
        }

