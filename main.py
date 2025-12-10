"""
Resume Ranking System - Main Entry Point

Full pipeline: Parse → Extract → Score → Rank → Display
"""

import argparse
import os
import json
from parser import parse_resume
from extractor import extract_structured_data
from scorer import ResumeScorer
from job_constants import JOB_DESCRIPTION


def get_args():
    parser = argparse.ArgumentParser(
        description="Resume Ranking System"
    )
    parser.add_argument("--files", nargs="*", help="Explicit resume file paths")
    parser.add_argument("--folder", help="Folder containing resume files")
    return parser.parse_args()


def collect_resume_files(args):
    """Collect resume files from CLI arguments (max 10)."""
    valid_ext = (".pdf", ".docx")

    if args.files:
        files = []
        for f in args.files:
            if not os.path.exists(f):
                print(f"Warning: File not found: {f}")
                continue
            if not f.lower().endswith(valid_ext):
                print(f"Warning: Skipping unsupported file type: {f}")
                continue
            files.append(f)
        return files[:10]
    
    if args.folder:
        if not os.path.isdir(args.folder):
            print("Error: Invalid folder path.")
            return []

        resume_files = []
        for fname in sorted(os.listdir(args.folder)):
            if fname.lower().endswith(valid_ext):
                full_path = os.path.join(args.folder, fname)
                if os.path.isfile(full_path):
                    resume_files.append(full_path)
                    if len(resume_files) == 10:
                        break
        return resume_files

    print("Error: Provide either --files or --folder")
    return []


def process_resume(file_path: str, scorer: ResumeScorer) -> dict:
    """Process a single resume through the full pipeline."""
    print(f"Processing: {os.path.basename(file_path)}:\n")
    
    # Step 1: Parse (extract text)
    print("Extracting text...")
    text = parse_resume(file_path)
    if not text:
        print("Failed to extract text!!")
        return None
    print(f"Extracted {len(text)} characters")
    
    # Step 2: Extract structured data
    print("Converting data to structured format")
    structured = extract_structured_data(text)
    if not structured:
        print("Failed to extract structured data!!")
        return None
    print(f"Extracted data for: {structured.get('name', 'Unknown')}")
    
    # Step 3: Score
    print("Calculating score...")
    score_result = scorer.score(structured)
    print(f"Score: {score_result['total_score']}")
    
    return {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        **score_result
    }


def display_rankings(results: list):
    """Display final ranked results."""
    print("FINAL RANKINGS: \n\n")
    
    for rank, result in enumerate(results, 1):
        print(f"\n{rank}. {result['file_name']} – Score: {result['total_score']}")
        print(f"   Candidate: {result['candidate_name']}")
        print(f"   {result['explanation']}")
        
        # Show breakdown
        breakdown = result['breakdown']
        print(f"   Breakdown: Skills={breakdown['skills']['score']:.1f} | "
              f"Experience={breakdown['experience']['score']:.1f} | "
              f"Relevance={breakdown['relevance']['score']:.1f} | "
              f"Education={breakdown['education']['score']:.1f}")
        
        # Show matched/missing skills
        details = result['details']
        if details['matched_skills']:
            print(f"   ✓ Matched skills: {', '.join(details['matched_skills'])}")
        if details['missing_skills']:
            print(f"   ✗ Missing skills: {', '.join(details['missing_skills'])}")


def main():
    """Main execution flow."""
    print("RESUME RANKING SYSTEM")
    
    # Get files
    args = get_args()
    resume_files = collect_resume_files(args)
    
    if not resume_files:
        print("No resume files to process.")
        return
    
    print(f"\nFound {len(resume_files)} resume(s) to process")
    print(f"Job Title: {JOB_DESCRIPTION['title']}")
    print(f"Required Skills: {', '.join(JOB_DESCRIPTION['required_skills'])}")
    print(f"Required Experience: {JOB_DESCRIPTION['required_experience']}+ years")
    
    # Initialize scorer
    scorer = ResumeScorer(JOB_DESCRIPTION)
    
    # Process all resumes
    results = []
    for file_path in resume_files:
        result = process_resume(file_path, scorer)
        if result:
            results.append(result)
    
    # Sort by score (descending)
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Display rankings
    if results:
        display_rankings(results)
        
        # Save to JSON
        output_file = "ranking_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, indent=2, fp=f)
        print(f"\n{'='*80}")
        print(f"Results saved to: {output_file}")
    else:
        print("\nNo resumes were successfully processed.")


if __name__ == "__main__":
    main()
