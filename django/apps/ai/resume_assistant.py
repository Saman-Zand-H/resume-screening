import json
import logging
from typing import List, Optional, Dict, Any, Union
import re

from google.genai.types import ContentListUnion, Content
from django.conf import settings

from .google import GoogleServices
from .assistants import Assistant
from .resume_models import ResumeAnalysisResult
from .types import FileType, FileToTextResult
from flex_blob.models import FileModel
from . import settings as resume_settings

logger = logging.getLogger(__name__)


class ResumeAnalysisAssistant(Assistant[ResumeAnalysisResult]):
    """
    Assistant for analyzing resumes using advanced NLP, NER, OCR, and specialized algorithms.
    Handles various resume formats, languages, and terminologies.
    """
    assistant_slug: str = "resume_analysis"
    
    def __init__(self, file_model_id: int = None, resume_text: str = None):
        """
        Initialize the resume analysis assistant with either a file or text.
        
        Args:
            file_model_id: ID of the uploaded resume file
            resume_text: Resume text if already extracted
        """
        super().__init__()
        self.file_model_id = file_model_id
        self.resume_text = resume_text
        self.file_type = None
        self.document_language = None
        
        # Results from various stages of processing
        self.extracted_text = None
        self.sections = {}
        self.ner_results = {}
        
        logger.debug(
            "ResumeAnalysisAssistant initialized", 
            extra={
                "has_file_id": bool(file_model_id),
                "has_text": bool(resume_text)
            }
        )
        
    def preprocess_resume(self) -> str:
        """
        Preprocess the resume by extracting text from various file formats.
        Uses OCR for images and PDFs, and appropriate parsers for other formats.
        
        Returns:
            Extracted and preprocessed text from the resume
        """
        logger.debug("Starting resume preprocessing")
        
        if self.resume_text:
            # Check if text is too long
            if len(self.resume_text) > resume_settings.MAX_RESUME_TEXT_LENGTH:
                logger.warning(
                    f"Resume text exceeds maximum length",
                    extra={
                        "actual_length": len(self.resume_text),
                        "max_length": resume_settings.MAX_RESUME_TEXT_LENGTH
                    }
                )
                self.resume_text = self.resume_text[:resume_settings.MAX_RESUME_TEXT_LENGTH]
                
            logger.debug("Using provided resume text")
            return self.resume_text
            
        if not self.file_model_id:
            logger.error("No file ID or resume text provided")
            raise ValueError("Either file_model_id or resume_text must be provided")
            
        # Get file model
        file_model = FileModel.objects.filter(pk=self.file_model_id).first()
        if not file_model:
            logger.error(f"File model with ID {self.file_model_id} not found")
            raise ValueError(f"File model with ID {self.file_model_id} not found")
            
        # Read file bytes
        try:
            with file_model.file.open("rb") as f:
                file_bytes = f.read()
                
            # Detect file type and extract text
            self.file_type = GoogleServices.detect_file_type(file_bytes)
            if not self.file_type:
                logger.error(f"Unsupported file type for file ID {self.file_model_id}")
                raise ValueError("Unsupported file type")
                
            logger.debug(f"Detected file type: {self.file_type.value}")
                
            # Extract text based on file type
            if self.file_type in [FileType.IMAGE, FileType.PDF]:
                # Use OCR for images and PDFs
                result = GoogleServices.file_to_text(file_bytes)
                if not result or not result.text:
                    logger.error(f"Failed to extract text from {self.file_type.value} file")
                    raise ValueError(f"Failed to extract text from {self.file_type.value} file")
                self.extracted_text = result.text
                logger.debug(f"Extracted text from {self.file_type.value} using OCR", extra={"text_length": len(self.extracted_text)})
            else:
                # For other file types, we might need specialized parsers
                logger.error(f"Parser for {self.file_type.value} not implemented yet")
                raise NotImplementedError(f"Parser for {self.file_type.value} not implemented yet")
                
            return self.extracted_text
            
        except Exception as e:
            logger.exception(f"Error processing resume file: {str(e)}")
            raise
        
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the resume text.
        
        Args:
            text: Resume text
            
        Returns:
            Detected language code
        """
        logger.debug("Detecting resume language")
        
        try:
            # Use the Google service to detect language
            prompts = [
                Content(
                    parts=[{"text": f"Detect the language of the following text and return just the language code (e.g., 'en', 'fr', 'es', etc.):\n\n{text[:1000]}"}],
                    role="user"
                )
            ]
            
            response = self.service.generate_text_content(prompts)
            # Extract language code - assuming response is just the language code
            language_code = response.strip().lower()
            self.document_language = language_code
            
            logger.debug(f"Detected language: {language_code}")
            return language_code
            
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            self.document_language = "unknown"
            return "unknown"
        
    def segment_resume(self, text: str) -> Dict[str, str]:
        """
        Segment the resume into different sections using Document Segmentation.
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary of sections and their content
        """
        logger.debug("Segmenting resume into sections")
        
        try:
            # Use the Google service to segment the resume
            prompts = [
                Content(
                    parts=[{
                        "text": f"""Segment the following resume into separate sections. 
                        Return a JSON object with keys for each section found in the resume, such as:
                        - contact_info
                        - summary
                        - education
                        - work_experience
                        - skills
                        - projects
                        - certifications
                        - languages
                        - references
                        
                        Resume text:
                        {text}
                        """
                    }],
                    role="user"
                )
            ]
            
            response = self.service.generate_text_content(prompts)
            
            # Extract JSON from the response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
                
            try:
                sections = json.loads(json_str)
                self.sections = sections
                
                logger.debug(
                    "Resume successfully segmented", 
                    extra={
                        "num_sections": len(sections),
                        "sections_found": list(sections.keys())
                    }
                )
                
                return sections
            except json.JSONDecodeError:
                logger.error("Failed to parse sections JSON", extra={"response": response[:100] + "..."})
                return {}
                
        except Exception as e:
            logger.error(f"Error during resume segmentation: {str(e)}")
            return {}
            
    def extract_entities(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract named entities from each resume section using NER.
        
        Args:
            sections: Dictionary of resume sections
            
        Returns:
            Dictionary of extracted entities for each section
        """
        logger.debug("Extracting entities from resume sections")
        results = {}
        
        for section_name, section_text in sections.items():
            if not section_text:
                continue
                
            logger.debug(f"Processing section: {section_name}")
                
            try:
                # Use the Google service to extract entities for each section
                prompts = [
                    Content(
                        parts=[{
                            "text": f"""Extract structured information from the following {section_name} section of a resume.
                            Return the result as a JSON object with appropriate fields based on the section type.
                            
                            Section type: {section_name}
                            Section content:
                            {section_text}
                            """
                        }],
                        role="user"
                    )
                ]
                
                response = self.service.generate_text_content(prompts)
                
                # Extract JSON from the response
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = response
                    
                try:
                    section_entities = json.loads(json_str)
                    results[section_name] = section_entities
                    logger.debug(f"Successfully extracted entities from {section_name}")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse entities JSON for {section_name}", extra={"response": response[:100] + "..."})
                    results[section_name] = {}
            
            except Exception as e:
                logger.error(f"Error extracting entities from {section_name}: {str(e)}")
                results[section_name] = {}
                
        self.ner_results = results
        
        logger.debug(
            "Entity extraction completed",
            extra={
                "sections_processed": len(sections),
                "entities_found": {k: bool(v) for k, v in results.items()}
            }
        )
        
        return results
        
    def standardize_dates(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize date formats across the resume using specialized date algorithms.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Dictionary with standardized dates
        """
        logger.debug("Standardizing date formats")
        
        try:
            # Create a copy of the entities dictionary to modify
            standardized = json.loads(json.dumps(entities))
            
            # Use the Google service to standardize dates
            prompts = [
                Content(
                    parts=[{
                        "text": f"""Standardize all dates in the following JSON data.
                        Convert all dates to YYYY-MM format.
                        For dates like "Present", "Current", "Now", "Today", etc., use "PRESENT".
                        Return the same JSON structure with standardized dates.
                        
                        JSON data:
                        {json.dumps(entities, indent=2)}
                        """
                    }],
                    role="user"
                )
            ]
            
            response = self.service.generate_text_content(prompts)
            
            # Extract JSON from the response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
                
            try:
                standardized = json.loads(json_str)
                logger.debug("Date standardization completed successfully")
            except json.JSONDecodeError:
                logger.error("Failed to parse standardized dates JSON", extra={"response": response[:100] + "..."})
                
            return standardized
            
        except Exception as e:
            logger.error(f"Error during date standardization: {str(e)}")
            return entities
        
    def standardize_skills(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize skill names using semantic similarity and ontology mapping.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Dictionary with standardized skills
        """
        logger.debug("Standardizing skills")
        
        try:
            # Create a copy of the entities dictionary to modify
            standardized = json.loads(json.dumps(entities))
            
            # Check if skills exist in the entities
            if "skills" not in entities:
                logger.debug("No skills section found, skipping skill standardization")
                return standardized
                
            # Use the Google service to standardize skills
            prompts = [
                Content(
                    parts=[{
                        "text": f"""Standardize the following skills from a resume.
                        Group similar skills (e.g., "Project Management" and "Leading Project Teams").
                        For each skill, provide:
                        1. A standardized name
                        2. The original text
                        3. A category (TECHNICAL, SOFT, LANGUAGE, DOMAIN, OTHER)
                        4. An estimated proficiency level (0-1) if possible
                        
                        Return a JSON array of standardized skills.
                        
                        Skills:
                        {json.dumps(entities["skills"], indent=2)}
                        """
                    }],
                    role="user"
                )
            ]
            
            response = self.service.generate_text_content(prompts)
            
            # Extract JSON from the response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
                
            try:
                standardized_skills = json.loads(json_str)
                standardized["skills"] = standardized_skills
                logger.debug(f"Skill standardization completed, found {len(standardized_skills)} skills")
            except json.JSONDecodeError:
                logger.error("Failed to parse standardized skills JSON", extra={"response": response[:100] + "..."})
                
            return standardized
            
        except Exception as e:
            logger.error(f"Error during skill standardization: {str(e)}")
            return entities
        
    def build_resume_analysis_result(self, standardized_entities: Dict[str, Any]) -> ResumeAnalysisResult:
        """
        Build the final ResumeAnalysisResult from standardized entities.
        
        Args:
            standardized_entities: Dictionary of standardized entities
            
        Returns:
            ResumeAnalysisResult object
        """
        logger.debug("Building final resume analysis result")
        
        try:
            # Use the Google service to transform the entities into the final result
            prompts = [
                Content(
                    parts=[{
                        "text": f"""Transform the following extracted resume information into a structured format.
                        Return a JSON object that exactly matches the schema of ResumeAnalysisResult with the following fields:
                        - contact_info (required): ContactInfo object with name, email, phone, location, links
                        - education (required): Array of Education objects
                        - work_experience (required): Array of WorkExperience objects
                        - skills (required): Array of Skill objects
                        - projects (optional): Array of Project objects
                        - certifications (optional): Array of Certification objects
                        - languages (optional): Array of Language objects
                        - extraction_confidence: Dictionary mapping section names to confidence scores (0-1)
                        - document_language: Detected language code
                        - file_format: File format of the original resume
                        - parsing_errors: Array of error messages (if any)
                        
                        Extracted information:
                        {json.dumps(standardized_entities, indent=2)}
                        
                        Document language: {self.document_language or "unknown"}
                        File format: {self.file_type.value if self.file_type else "unknown"}
                        """
                    }],
                    role="user"
                )
            ]
            
            response = self.service.generate_text_content(prompts)
            
            # Extract JSON from the response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
                
            try:
                result_dict = json.loads(json_str)
                result = ResumeAnalysisResult(**result_dict)
                logger.debug(
                    "Resume analysis result built successfully",
                    extra={
                        "has_contact": bool(result.contact_info and result.contact_info.name),
                        "education_count": len(result.education),
                        "work_experience_count": len(result.work_experience),
                        "skills_count": len(result.skills)
                    }
                )
                return result
            except Exception as e:
                logger.error(f"Failed to build ResumeAnalysisResult: {str(e)}")
                # Return a minimal valid result
                error_msg = f"Failed to build result: {str(e)}"
                logger.warning(f"Returning minimal result with error: {error_msg}")
                return ResumeAnalysisResult(
                    contact_info={"name": "Unknown"},
                    education=[],
                    work_experience=[],
                    skills=[],
                    parsing_errors=[error_msg]
                )
        except Exception as e:
            logger.exception(f"Critical error building resume result: {str(e)}")
            return ResumeAnalysisResult(
                contact_info={"name": "Unknown"},
                education=[],
                work_experience=[],
                skills=[],
                parsing_errors=[f"Critical error: {str(e)}"]
            )
    
    def get_prompts(self, *args, **kwargs) -> ContentListUnion:
        """
        Get prompts for the resume analysis pipeline.
        
        Returns:
            ContentListUnion for the Google API
        """
        logger.info("Executing resume analysis pipeline")
        
        try:
            # Process the resume
            text = self.preprocess_resume()
            self.detect_language(text)
            sections = self.segment_resume(text)
            entities = self.extract_entities(sections)
            standardized_dates = self.standardize_dates(entities)
            standardized_entities = self.standardize_skills(standardized_dates)
            
            result = self.build_resume_analysis_result(standardized_entities)
            
            logger.info("Resume analysis pipeline completed successfully")
            
            # Return the result as a JSON string
            return [
                Content(
                    parts=[{"text": json.dumps(result.dict(), indent=2)}],
                    role="model"
                )
            ]
        
        except Exception as e:
            logger.exception(f"Error in resume analysis pipeline: {str(e)}")
            
            # Return an error message
            error_response = {
                "error": str(e),
                "status": "failed"
            }
            
            logger.error("Returning error response", extra={"error": str(e)})
            
            return [
                Content(
                    parts=[{"text": json.dumps(error_response, indent=2)}],
                    role="model"
                )
            ]
    
    def should_pass(self, result: ResumeAnalysisResult):
        """
        Check if the resume analysis result is valid and meets quality thresholds.
        
        Args:
            result: ResumeAnalysisResult to check
            
        Returns:
            True if the result passes quality checks, False otherwise
        """
        # Check for required sections
        for section in resume_settings.REQUIRED_RESUME_SECTIONS:
            if section == "contact_info":
                if not result.contact_info or not result.contact_info.name:
                    logger.warning("Resume result failed validation: missing contact info")
                    return False
            elif section == "education" and (not result.education or len(result.education) == 0):
                logger.warning("Resume result failed validation: missing education")
                return False
            elif section == "work_experience" and (not result.work_experience or len(result.work_experience) == 0):
                logger.warning("Resume result failed validation: missing work experience")
                return False
            elif section == "skills" and (not result.skills or len(result.skills) == 0):
                logger.warning("Resume result failed validation: missing skills")
                return False
                
        # Check if there are any parsing errors
        if result.parsing_errors and len(result.parsing_errors) > 0:
            logger.warning("Resume result failed validation: has parsing errors", extra={"errors": result.parsing_errors})
            return False
            
        # Check overall extraction confidence
        avg_confidence = sum(result.extraction_confidence.values()) / len(result.extraction_confidence)
        if avg_confidence < resume_settings.RESUME_ANALYSIS_THRESHOLD:
            logger.warning(f"Resume result failed validation: confidence below threshold", extra={"confidence": avg_confidence})
            return False
            
        logger.info("Resume result passed validation", extra={"avg_confidence": avg_confidence})
        return True
        
    def response_builder(self, results: str, *, old_results: List[dict] = []) -> ResumeAnalysisResult:
        """
        Build the final response from the generated text.
        
        Args:
            results: String response from the model
            old_results: Previous results from pipeline
            
        Returns:
            ResumeAnalysisResult object
        """
        logger.debug("Building response from model output")
        
        try:
            # Try to parse the results as JSON
            json_data = json.loads(results)
            result = ResumeAnalysisResult(**json_data)
            logger.debug("Successfully parsed model response as ResumeAnalysisResult")
            return result
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse response as JSON: {str(e)}", extra={"response_preview": results[:100] + "..."})
            # Use the super implementation as fallback
            logger.warning("Falling back to default response builder")
            return super().response_builder(results, old_results=old_results) 