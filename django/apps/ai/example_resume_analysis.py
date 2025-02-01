"""
Django utility module for resume analysis operations.

Provides utilities for resume analysis, validation, and reporting.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from django.core.files.base import ContentFile
from flex_blob.models import FileModel

from .resume_pipeline import ResumeAnalysisPipeline
from .resume_models import ResumeAnalysisResult
from . import settings as resume_settings

logger = logging.getLogger(__name__)


def analyze_resume_from_file(file_path: str) -> ResumeAnalysisPipeline:
    """
    Analyze a resume from a file on disk.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        ResumeAnalysisPipeline instance with analysis results
    """
    path = Path(file_path)
    
    try:
        with open(path, 'rb') as f:
            file_content = f.read()
            
        # Check file size
        if len(file_content) > resume_settings.MAX_RESUME_FILE_SIZE:
            logger.warning(
                f"Resume file exceeds maximum size",
                extra={
                    "file_path": path,
                    "file_size": len(file_content),
                    "max_size": resume_settings.MAX_RESUME_FILE_SIZE
                }
            )
            raise ValueError(f"Resume file exceeds maximum size of {resume_settings.MAX_RESUME_FILE_SIZE} bytes")
        
        # Check file extension
        file_ext = path.suffix[1:].lower()
        if file_ext not in resume_settings.SUPPORTED_RESUME_FILE_TYPES:
            logger.warning(
                f"Unsupported resume file type",
                extra={
                    "file_path": path,
                    "file_extension": file_ext,
                    "supported_types": resume_settings.SUPPORTED_RESUME_FILE_TYPES
                }
            )
            raise ValueError(f"Unsupported resume file type: {file_ext}")
        
        file_model = FileModel.objects.create(
            file=ContentFile(file_content, name=path.name),
            file_name=path.name,
            mime_type=f"application/{file_ext}",
        )
        
        pipeline = ResumeAnalysisPipeline(file_model_id=file_model.id)
        pipeline.analyze_resume()
        
        logger.info(
            "Resume analyzed successfully", 
            extra={
                "file_name": path.name,
                "skills_count": len(pipeline.results.skills),
                "education_count": len(pipeline.results.education),
                "experience_count": len(pipeline.results.work_experience),
                "file_size": len(file_content)
            }
        )
        
        return pipeline
    
    except Exception as e:
        logger.error(f"Error analyzing resume from file: {str(e)}", extra={"file_path": file_path})
        raise


def analyze_resume_from_text(resume_text: str) -> ResumeAnalysisPipeline:
    """
    Analyze a resume from raw text.
    
    Args:
        resume_text: Raw text of the resume
        
    Returns:
        ResumeAnalysisPipeline instance with analysis results
    """
    try:
        # Check text length
        if len(resume_text) > resume_settings.MAX_RESUME_TEXT_LENGTH:
            logger.warning(
                f"Resume text exceeds maximum length",
                extra={
                    "text_length": len(resume_text),
                    "max_length": resume_settings.MAX_RESUME_TEXT_LENGTH
                }
            )
            resume_text = resume_text[:resume_settings.MAX_RESUME_TEXT_LENGTH]
            logger.info(f"Resume text truncated to {resume_settings.MAX_RESUME_TEXT_LENGTH} characters")
        
        pipeline = ResumeAnalysisPipeline(resume_text=resume_text)
        pipeline.analyze_resume()
        
        logger.info(
            "Resume text analyzed successfully", 
            extra={
                "text_length": len(resume_text),
                "skills_count": len(pipeline.results.skills),
                "education_count": len(pipeline.results.education),
                "experience_count": len(pipeline.results.work_experience)
            }
        )
        
        return pipeline
    
    except Exception as e:
        logger.error(f"Error analyzing resume from text: {str(e)}")
        raise


def evaluate_against_ground_truth(
    pipeline: ResumeAnalysisPipeline, 
    ground_truth_file: Optional[str] = None
) -> Dict[str, float]:
    """
    Evaluate the resume analysis results against ground truth data.
    
    Args:
        pipeline: ResumeAnalysisPipeline instance with results
        ground_truth_file: Path to a JSON file with ground truth data
        
    Returns:
        Dictionary with accuracy metrics
    """
    try:
        if ground_truth_file:
            with open(ground_truth_file, 'r') as f:
                ground_truth = json.load(f)
        else:
            # Default ground truth data for testing/example purposes
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
        
        accuracy = pipeline.evaluate_accuracy(ground_truth)
        
        logger.info(
            "Resume evaluation completed",
            extra={
                "overall_accuracy": accuracy.get("overall", 0),
                "metrics": accuracy
            }
        )
        
        return accuracy
    
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        raise


def generate_report(
    pipeline: ResumeAnalysisPipeline, 
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a report on the resume analysis results and optionally save to a file.
    
    Args:
        pipeline: ResumeAnalysisPipeline instance with results
        output_file: Path to save the report JSON
        
    Returns:
        Dictionary with report data
    """
    try:
        report = pipeline.generate_report()
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
                logger.info(f"Report saved to {output_file}")
        
        # Get language name from code
        language_code = report.get("language", {}).get("code", "unknown")
        language_name = report.get("language", {}).get("name", language_code)
        
        logger.info(
            "Report generated successfully",
            extra={
                "language": language_name,
                "contact_info_found": report.get("extraction", {}).get("contact_info", {}).get("found", False),
                "skills_count": report.get("extraction", {}).get("skills", {}).get("count", 0),
                "missing_sections": report.get("missing_sections", []),
                "errors": len(report.get("errors", []))
            }
        )
        
        return report
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise 