"""
Example script demonstrating how to use the Resume Analysis System.

This script shows how to:
1. Analyze a resume from a file or text
2. Evaluate accuracy against ground truth data
3. Generate and display a report
"""

import json
import logging
from pathlib import Path

from django.core.files.base import ContentFile
from flex_blob.models import FileModel

from .resume_pipeline import ResumeAnalysisPipeline
from .resume_models import ResumeAnalysisResult

logger = logging.getLogger(__name__)


def analyze_resume_from_file(file_path):
    """
    Analyze a resume from a file on disk.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        ResumeAnalysisPipeline instance with results
    """
    # Read file
    path = Path(file_path)
    with open(path, 'rb') as f:
        file_content = f.read()
    
    # Create a FileModel instance
    file_model = FileModel.objects.create(
        file=ContentFile(file_content, name=path.name),
        file_name=path.name,
        mime_type=f"application/{path.suffix[1:]}",  # Simple mime type guess
    )
    
    # Create and run the pipeline
    pipeline = ResumeAnalysisPipeline(file_model_id=file_model.id)
    result = pipeline.analyze_resume()
    
    print(f"Analyzed resume: {path.name}")
    print(f"Extracted {len(result.skills)} skills")
    print(f"Found {len(result.education)} education entries")
    print(f"Found {len(result.work_experience)} work experiences")
    
    return pipeline


def analyze_resume_from_text(resume_text):
    """
    Analyze a resume from raw text.
    
    Args:
        resume_text: Raw text of the resume
        
    Returns:
        ResumeAnalysisPipeline instance with results
    """
    # Create and run the pipeline with text
    pipeline = ResumeAnalysisPipeline(resume_text=resume_text)
    result = pipeline.analyze_resume()
    
    print(f"Analyzed resume text ({len(resume_text)} characters)")
    print(f"Extracted {len(result.skills)} skills")
    print(f"Found {len(result.education)} education entries")
    print(f"Found {len(result.work_experience)} work experiences")
    
    return pipeline


def evaluate_against_ground_truth(pipeline, ground_truth_file=None):
    """
    Evaluate the resume analysis results against ground truth data.
    
    Args:
        pipeline: ResumeAnalysisPipeline instance with results
        ground_truth_file: Path to a JSON file with ground truth data
        
    Returns:
        Dictionary with accuracy metrics
    """
    # Load ground truth data
    if ground_truth_file:
        with open(ground_truth_file, 'r') as f:
            ground_truth = json.load(f)
    else:
        # Example ground truth data
        ground_truth = {
            "contact_info": {
                "name": "Jane Doe",
                "email": "jane.doe@example.com",
                "phone": "+1 (555) 123-4567",
                "location": "New York, NY"
            },
            "education": [
                {
                    "institution": "Columbia University",
                    "degree": "Master of Science",
                    "field_of_study": "Computer Science",
                    "start_date": "2018-09",
                    "end_date": "2020-05"
                },
                {
                    "institution": "University of California, Berkeley",
                    "degree": "Bachelor of Science",
                    "field_of_study": "Computer Engineering",
                    "start_date": "2014-09",
                    "end_date": "2018-05"
                }
            ],
            "work_experience": [
                {
                    "company": "Tech Innovations Inc.",
                    "position": "Senior Software Engineer",
                    "start_date": "2020-06",
                    "end_date": "PRESENT",
                    "responsibilities": [
                        "Lead a team of 5 engineers",
                        "Develop cloud-based solutions",
                        "Implement CI/CD pipelines"
                    ]
                },
                {
                    "company": "Data Systems LLC",
                    "position": "Software Engineer",
                    "start_date": "2018-06",
                    "end_date": "2020-05",
                    "responsibilities": [
                        "Developed RESTful APIs",
                        "Implemented machine learning models",
                        "Optimized database queries"
                    ]
                }
            ],
            "skills": [
                {
                    "name": "Python",
                    "category": "TECHNICAL"
                },
                {
                    "name": "Machine Learning",
                    "category": "TECHNICAL"
                },
                {
                    "name": "Project Management",
                    "category": "SOFT"
                }
            ]
        }
    
    # Evaluate accuracy
    accuracy = pipeline.evaluate_accuracy(ground_truth)
    
    print("\nAccuracy Evaluation:")
    for section, score in accuracy.items():
        print(f"  {section}: {score * 100:.1f}%")
    
    return accuracy


def generate_and_save_report(pipeline, output_file=None):
    """
    Generate a report on the resume analysis results and optionally save to a file.
    
    Args:
        pipeline: ResumeAnalysisPipeline instance with results
        output_file: Path to save the report JSON
        
    Returns:
        Dictionary with report data
    """
    # Generate report
    report = pipeline.generate_report()
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    print("\nReport:")
    print(f"  Language: {report['language']}")
    print(f"  Format: {report['format']}")
    print(f"  Contact Info Found: {report['extraction']['contact_info']['found']}")
    print(f"  Education Entries: {report['extraction']['education']['count']}")
    print(f"  Work Experiences: {report['extraction']['work_experience']['count']}")
    print(f"  Skills Found: {report['extraction']['skills']['count']}")
    
    if 'accuracy' in report:
        print(f"  Overall Accuracy: {report['accuracy']['overall'] * 100:.1f}%")
    
    return report


def main():
    """Main function demonstrating the resume analysis process."""
    # Example 1: Analyze a resume from a file
    # pipeline = analyze_resume_from_file("path/to/resume.pdf")
    
    # Example 2: Analyze a resume from text
    sample_resume = """
    JANE DOE
    New York, NY | (555) 123-4567 | jane.doe@example.com | linkedin.com/in/janedoe
    
    EDUCATION
    Columbia University, New York, NY
    Master of Science in Computer Science, GPA: 3.8/4.0
    September 2018 - May 2020
    
    University of California, Berkeley, CA
    Bachelor of Science in Computer Engineering, GPA: 3.7/4.0
    September 2014 - May 2018
    
    WORK EXPERIENCE
    Tech Innovations Inc., New York, NY
    Senior Software Engineer
    June 2020 - Present
    • Lead a team of 5 engineers developing cloud-based solutions
    • Implement CI/CD pipelines, reducing deployment time by 40%
    • Architect and develop microservices using Python, Docker, and Kubernetes
    
    Data Systems LLC, San Francisco, CA
    Software Engineer
    June 2018 - May 2020
    • Developed RESTful APIs using Django and Flask
    • Implemented machine learning models for predictive analytics
    • Optimized SQL queries, improving application performance by 30%
    
    SKILLS
    Languages: Python, Java, JavaScript, SQL, C++
    Frameworks: Django, Flask, React, TensorFlow
    Tools: Docker, Kubernetes, Git, CI/CD, AWS, GCP
    Soft Skills: Project Management, Team Leadership, Communication
    """
    
    pipeline = analyze_resume_from_text(sample_resume)
    
    # Evaluate against ground truth
    evaluate_against_ground_truth(pipeline)
    
    # Generate and save report
    generate_and_save_report(pipeline, "resume_analysis_report.json")


if __name__ == "__main__":
    main() 