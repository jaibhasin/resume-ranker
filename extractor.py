"""
Resume Extractor: Converts raw resume text to structured JSON using Gemini.
Uses structured output with Pydantic schemas for deterministic extraction.
"""

import os
import json
from typing import Optional
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# Pydantic schemas for structured output
class Experience(BaseModel):
    job_title: str = Field(description="Job title/role")
    company: str = Field(description="Company name")
    duration: str = Field(description="Duration (e.g., 'Jan 2020 - Dec 2022')")
    years: float = Field(description="Approximate years at this job")
    responsibilities: list[str] = Field(description="Key responsibilities/achievements")


class Education(BaseModel):
    degree: str = Field(description="Degree name")
    institution: str = Field(description="University/College name")
    year: str = Field(description="Graduation year or duration")


class ResumeData(BaseModel):
    name: str = Field(description="Candidate's full name")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    location: str = Field(description="City/Location")
    summary: str = Field(description="Professional summary or objective")
    skills: list[str] = Field(description="List of technical and soft skills")
    experience: list[Experience] = Field(description="Work experience list")
    education: list[Education] = Field(description="Education history")
    certifications: list[str] = Field(description="Certifications and courses")
    total_years_experience: float = Field(description="Total years of professional experience")


def extract_structured_data(resume_text: str) -> Optional[dict]:
    """Extract structured data from resume text using Gemini."""
    try:
        model = genai.GenerativeModel(
            "gemini-2.5-flash-lite",
            generation_config=genai.GenerationConfig(
                temperature=0,  # Deterministic
                response_mime_type="application/json",
                response_schema=ResumeData
            )
        )
        
        prompt = f"""Analyze this resume and extract structured information.
        
RESUME TEXT:
{resume_text}

Extract all relevant information accurately. For missing fields, use empty strings or empty lists.
Calculate total_years_experience by summing up all job durations."""

        response = model.generate_content(prompt)
        
        if response.text:
            return json.loads(response.text)
        return None
        
    except Exception as e:
        print(f"Error extracting structured data: {e}")
        return None

