"""
Resume Scorer: Deterministic scoring using LLM-based skill matching.
Uses Gemini 2.5 Flash with temperature=0 for reproducible results.
"""

import os
import json
from typing import Dict, List, Any, Tuple
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# Pydantic schema for skill matching response
class SkillMatchResult(BaseModel):
    matched_skills: List[str] = Field(description="List of required skills that candidate satisfies")
    reasoning: str = Field(description="Brief explanation of skill matching")


def match_skills_with_llm(candidate_skills: List[str], required_skills: List[str]) -> Tuple[List[str], str]:
    """
    Use Gemini to intelligently match candidate skills to required skills.
    Handles semantic equivalence (Flask → Python, EC2 → AWS, etc.)
    """
    if not candidate_skills or not required_skills:
        return [], "No skills to match"
    
    try:
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config=genai.GenerationConfig(
                temperature=0,  # Deterministic
                response_mime_type="application/json",
                response_schema=SkillMatchResult
            )
        )
        
        prompt = f"""Analyze the candidate's skills and determine which REQUIRED skills they satisfy.

REQUIRED SKILLS: {json.dumps(required_skills)}

CANDIDATE'S SKILLS: {json.dumps(candidate_skills)}

Rules:
- A candidate skill can satisfy a required skill if it's the same technology OR a related framework/tool
- Examples: "Flask" satisfies "python", "React Native" satisfies "javascript", "PostgreSQL" satisfies "sql", "EC2" satisfies "aws"
- Only return skills from the REQUIRED SKILLS list that are satisfied
- Be strict but fair - the candidate should have clear knowledge of the technology

Return the matched required skills and brief reasoning."""

        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        # Normalize matched skills to lowercase
        matched = [s.lower() for s in result.get('matched_skills', [])]
        reasoning = result.get('reasoning', '')
        
        # Filter to only include valid required skills
        valid_matched = [s for s in matched if s in [r.lower() for r in required_skills]]
        
        return valid_matched, reasoning
        
    except Exception as e:
        print(f"Error in LLM skill matching: {e}")
        # Fallback to simple exact matching
        candidate_lower = {s.lower() for s in candidate_skills}
        required_lower = {s.lower() for s in required_skills}
        return list(candidate_lower.intersection(required_lower)), "Fallback: exact match only"


class ResumeScorer:
    """Deterministic resume scoring engine with LLM-based skill matching."""
    
    def __init__(self, job_description: Dict[str, Any]):
        self.jd = job_description
        self.job_title = job_description.get('title', '').lower()
        self.required_experience = job_description.get('required_experience', 0)
        self.required_skills = [s.lower() for s in job_description.get('required_skills', [])]
        
        # Weights for scoring (total = 100)
        self.weights = {
            'skills': 40,
            'experience': 30,
            'relevance': 20,
            'education': 10
        }
    
    def calculate_skills_score(self, candidate_skills: List[str]) -> Tuple[float, List[str], List[str], str]:
        """Calculate skills score using LLM matching."""
        if not self.required_skills:
            return 100.0, [], [], "No skills required"
        
        if not candidate_skills:
            return 0.0, [], self.required_skills, "No skills provided"
        
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
            score = (years / req) * 100
            explanation = f"{years:.1f}y (need {req}+)"
        else:
            score = 100.0
            explanation = f"{years:.1f}y (meets {req}+ req)"
        
        return score, explanation
    
    def calculate_relevance_score(self, experience: List[Dict]) -> Tuple[float, str]:
        """Calculate role relevance from job titles."""
        if not experience:
            return 0.0, "No work history"
        
        relevant_keywords = {
            'software', 'developer', 'engineer', 'programmer', 'full-stack',
            'fullstack', 'backend', 'frontend', 'front-end', 'back-end',
            'web', 'application', 'tech lead', 'devops', 'sre', 'architect'
        }
        
        relevant = sum(1 for exp in experience 
                      if any(kw in exp.get('job_title', '').lower() for kw in relevant_keywords))
        total = len(experience)
        
        score = (relevant / total) * 100 if total > 0 else 0
        return score, f"{relevant}/{total} relevant roles"
    
    def calculate_education_score(self, education: List[Dict]) -> Tuple[float, str]:
        """Calculate education score with tiered degrees."""
        if not education:
            return 30.0, "No education listed"
        
        tier1 = ['computer science', 'software engineering', 'computer engineering']
        tier2 = ['information technology', 'data science', 'electrical engineering', 'mathematics']
        tier3 = ['engineering', 'science', 'technology']
        
        best_score, best_note = 30.0, "No relevant degree"
        
        for edu in education:
            degree = edu.get('degree', '').lower()
            if any(t in degree for t in tier1):
                return 100.0, "CS/SE degree"
            elif any(t in degree for t in tier2):
                if 80.0 > best_score:
                    best_score, best_note = 80.0, "Related technical degree"
            elif any(t in degree for t in tier3):
                if 60.0 > best_score:
                    best_score, best_note = 60.0, "Technical degree"
            elif 'bachelor' in degree or 'master' in degree:
                if 50.0 > best_score:
                    best_score, best_note = 50.0, "Other degree"
        
        return best_score, best_note
    
    def score(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total weighted score."""
        skills = resume_data.get('skills', [])
        years = resume_data.get('total_years_experience', 0)
        experience = resume_data.get('experience', [])
        education = resume_data.get('education', [])
        name = resume_data.get('name', 'Unknown')
        
        # Calculate scores
        skills_score, matched, missing, skill_reasoning = self.calculate_skills_score(skills)
        exp_score, exp_note = self.calculate_experience_score(years)
        rel_score, rel_note = self.calculate_relevance_score(experience)
        edu_score, edu_note = self.calculate_education_score(education)
        
        # Weighted total
        total = (
            (skills_score * self.weights['skills'] / 100) +
            (exp_score * self.weights['experience'] / 100) +
            (rel_score * self.weights['relevance'] / 100) +
            (edu_score * self.weights['education'] / 100)
        )
        
        # Generate explanation
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
                "skill_reasoning": skill_reasoning,
                "experience_years": years,
                "education_note": edu_note
            }
        }


if __name__ == "__main__":
    from job_constants import JOB_DESCRIPTION
    
    scorer = ResumeScorer(JOB_DESCRIPTION)
    
    # Test - Flask should match Python!
    sample = {
        "name": "Test Candidate",
        "skills": ["Flask", "Django", "TypeScript", "EC2", "GitHub", "PostgreSQL"],
        "total_years_experience": 4,
        "experience": [{"job_title": "Software Engineer"}],
        "education": [{"degree": "BS Computer Science"}]
    }
    
    result = scorer.score(sample)
    print(json.dumps(result, indent=2))
