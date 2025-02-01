import logging
from typing import Optional, Dict, Any, List

from .assistants import AssistantPipeline
from .resume_assistant import ResumeAnalysisAssistant
from .resume_models import ResumeAnalysisResult
from . import settings as resume_settings

logger = logging.getLogger(__name__)


class ResumeAnalysisPipeline:
    """
    Pipeline for analyzing resumes using the ResumeAnalysisAssistant.
    Provides high-level methods for resume analysis and testing.
    """
    
    def __init__(self, file_model_id: Optional[int] = None, resume_text: Optional[str] = None):
        """
        Initialize the resume analysis pipeline.
        
        Args:
            file_model_id: ID of the uploaded resume file
            resume_text: Resume text if already extracted
        """
        self.file_model_id = file_model_id
        self.resume_text = resume_text
        self.results: Optional[ResumeAnalysisResult] = None
        self.accuracy_metrics: Dict[str, float] = {}
        
    def analyze_resume(self) -> ResumeAnalysisResult:
        """
        Analyze a resume using the ResumeAnalysisAssistant.
        
        Returns:
            ResumeAnalysisResult with extracted information
        """
        logger.debug("Starting resume analysis process")
        
        assistant = ResumeAnalysisAssistant(
            file_model_id=self.file_model_id,
            resume_text=self.resume_text
        )
        
        pipeline = AssistantPipeline(assistant)
        
        result = pipeline.run()
        self.results = result
        
        logger.info(
            "Resume analysis completed successfully",
            extra={
                "has_contact": bool(result.contact_info and result.contact_info.name),
                "education_count": len(result.education),
                "work_experience_count": len(result.work_experience),
                "skills_count": len(result.skills)
            }
        )
        
        return result
        
    def evaluate_accuracy(self, ground_truth: Dict[str, Any]) -> Dict[str, float]:
        """
        Evaluate the accuracy of the resume analysis against ground truth.
        
        Args:
            ground_truth: Dictionary with ground truth data for comparison
            
        Returns:
            Dictionary with accuracy metrics for each section
        """
        if not self.results:
            logger.error("Cannot evaluate accuracy without results")
            raise ValueError("No results to evaluate. Run analyze_resume() first.")
            
        metrics = {}
        
        # Convert results to dictionary for easier comparison
        results_dict = self.results.dict()
        
        logger.debug("Starting accuracy evaluation")
        
        # Calculate accuracy for each section
        for section in ["contact_info", "education", "work_experience", "skills"]:
            if section in ground_truth and section in results_dict:
                # Calculate section accuracy
                correct = 0
                total = 0
                
                if section == "contact_info":
                    # For contact info, check each field individually
                    gt_contact = ground_truth[section]
                    result_contact = results_dict[section]
                    
                    for field in ["name", "email", "phone", "location"]:
                        if field in gt_contact and field in result_contact:
                            if gt_contact[field] == result_contact[field]:
                                correct += 1
                            total += 1
                
                elif isinstance(ground_truth[section], list) and isinstance(results_dict[section], list):
                    # For lists (like education, work_experience), count matching items
                    total = len(ground_truth[section])
                    
                    # Count exact matches
                    for gt_item in ground_truth[section]:
                        for result_item in results_dict[section]:
                            if self._item_match(gt_item, result_item):
                                correct += 1
                                break
                
                if total > 0:
                    metrics[section] = correct / total
                else:
                    metrics[section] = 0.0
                
                logger.debug(
                    f"Calculated accuracy for {section}", 
                    extra={"accuracy": metrics[section], "correct": correct, "total": total}
                )
        
        # Calculate overall accuracy
        if metrics:
            metrics["overall"] = sum(metrics.values()) / len(metrics)
        else:
            metrics["overall"] = 0.0
            
        logger.info(
            "Accuracy evaluation completed", 
            extra={"overall_accuracy": metrics.get("overall", 0)}
        )
            
        self.accuracy_metrics = metrics
        return metrics
    
    def _item_match(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> bool:
        """
        Check if two items match based on key fields.
        
        Args:
            item1: First item to compare
            item2: Second item to compare
            
        Returns:
            True if items match, False otherwise
        """
        # Check if the primary key fields match
        for key in item1:
            if key in item2:
                if isinstance(item1[key], str) and isinstance(item2[key], str):
                    # For strings, check similarity
                    similarity = self._string_similarity(item1[key], item2[key])
                    if similarity < 0.8:  # 80% similarity threshold
                        return False
                elif item1[key] != item2[key]:
                    return False
        
        return True
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        # Normalize strings
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        # If both are empty, they're the same
        if not s1 and not s2:
            return 1.0
            
        # If one is empty, they're totally different
        if not s1 or not s2:
            return 0.0
            
        # Count same characters
        common_chars = sum(1 for c in s1 if c in s2)
        
        # Similarity is common chars / total unique chars
        total_chars = len(set(s1 + s2))
        if total_chars == 0:
            return 0.0
            
        return common_chars / total_chars
        
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a detailed report on the resume analysis results.
        
        Returns:
            Dictionary with report data
        """
        if not self.results:
            logger.error("Cannot generate report without results")
            raise ValueError("No results to report. Run analyze_resume() first.")
            
        logger.debug("Generating resume analysis report")
        
        # Map language code to language name if available
        language_name = resume_settings.LANGUAGE_MAPPING.get(
            self.results.document_language, 
            self.results.document_language
        )
        
        report = {
            "extraction": {
                "contact_info": {
                    "found": bool(self.results.contact_info and self.results.contact_info.name),
                    "confidence": self.results.extraction_confidence.get("contact_info", 0.0)
                },
                "education": {
                    "count": len(self.results.education),
                    "confidence": self.results.extraction_confidence.get("education", 0.0)
                },
                "work_experience": {
                    "count": len(self.results.work_experience),
                    "confidence": self.results.extraction_confidence.get("work_experience", 0.0)
                },
                "skills": {
                    "count": len(self.results.skills),
                    "confidence": self.results.extraction_confidence.get("skills", 0.0)
                }
            },
            "language": {
                "code": self.results.document_language,
                "name": language_name
            },
            "format": self.results.file_format,
            "errors": self.results.parsing_errors or [],
            "missing_sections": self._get_missing_sections()
        }
        
        # Add accuracy metrics if available
        if self.accuracy_metrics:
            report["accuracy"] = self.accuracy_metrics
            
        logger.info("Resume analysis report generated successfully")
            
        return report
        
    def _get_missing_sections(self) -> List[str]:
        """
        Check for missing or empty sections in the results.
        
        Returns:
            List of section names that are missing or empty
        """
        missing = []
        
        if not self.results.contact_info or not self.results.contact_info.name:
            missing.append("contact_info")
        
        if not self.results.education:
            missing.append("education")
            
        if not self.results.work_experience:
            missing.append("work_experience")
            
        if not self.results.skills:
            missing.append("skills")
            
        # Optional sections
        if resume_settings.REQUIRED_RESUME_SECTIONS.count("projects") > 0 and not self.results.projects:
            missing.append("projects")
            
        if resume_settings.REQUIRED_RESUME_SECTIONS.count("certifications") > 0 and not self.results.certifications:
            missing.append("certifications")
            
        if resume_settings.REQUIRED_RESUME_SECTIONS.count("languages") > 0 and not self.results.languages:
            missing.append("languages")
            
        return missing


# Example usage:
# pipeline = ResumeAnalysisPipeline(file_model_id=123)
# result = pipeline.analyze_resume()
# print(f"Extracted {len(result.skills)} skills from resume")
#
# # Evaluate accuracy against ground truth
# ground_truth = {...}  # Ground truth data
# accuracy = pipeline.evaluate_accuracy(ground_truth)
# print(f"Overall accuracy: {accuracy['overall'] * 100:.1f}%")
#
# # Generate report
# report = pipeline.generate_report()
# print(f"Report: {report}") 