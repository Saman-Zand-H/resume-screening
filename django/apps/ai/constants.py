from typing import Dict, List, Pattern, Set, Tuple
import re

from .types import EntityType, FileType, ResumeSection

# File type mappings for AI-based document analysis
# These mappings are used to determine the processing method for different file formats
# Based on our AI Resume Analysis System that handles documents in multiple formats
FILE_TYPE_MAPPING = {
    # Image formats - processed with OCR and NER for text extraction
    "image/": FileType.IMAGE,  # All image MIME types (jpg, png, etc.)
    "image/jpeg": FileType.IMAGE,
    "image/png": FileType.IMAGE,
    "image/tiff": FileType.OCR_REQUIRED,  # Scanned documents often use TIFF format
    
    # Document formats
    "application/pdf": FileType.PDF,  # PDF documents
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX,  # DOCX (Word)
    "application/msword": FileType.DOC,  # DOC (Legacy Word)
    "text/plain": FileType.TXT,  # Plain text files
    "application/rtf": FileType.RTF,  # Rich Text Format
    
    # Special cases requiring OCR
    "application/octet-stream": FileType.OCR_REQUIRED,  # Binary files needing OCR analysis
}

# NLP and NER Constants
# =====================

# Confidence thresholds
NER_CONFIDENCE_THRESHOLD = 0.85  # Minimum confidence score for NER predictions
SKILL_MAPPING_CONFIDENCE = 0.75  # Threshold for skill term standardization

# NLP Models configuration
NLP_MODELS = {
    "resume_ner": "resume-ner-v2",  # Our custom NER model for resume parsing
    "multilingual": "mgpt-resume-v1",  # Multilingual model for non-English resumes
    "skill_standardization": "skill-bert-v3",  # Model for standardizing skill terms
    "section_classifier": "resume-section-classifier-v2",  # Model for identifying resume sections
}

# Target accuracy goals for each entity type based on project milestones
TARGET_ACCURACY = {
    EntityType.NAME: 98.0,
    EntityType.JOB_TITLE: 95.0,
    EntityType.EDUCATION: 98.0,
    EntityType.SKILL: 96.0,
    EntityType.DATE: 99.0,
    EntityType.CERTIFICATION: 94.0,
    EntityType.LANGUAGE: 97.0,
}

# Resume Section Detection
# =======================

# Common section headers in resumes (used for section detection)
SECTION_HEADERS = {
    ResumeSection.PERSONAL_INFO: [
        "personal information", "contact", "contact information", "personal details"
    ],
    ResumeSection.WORK_EXPERIENCE: [
        "work experience", "professional experience", "employment history", 
        "work history", "experience", "professional background", "career"
    ],
    ResumeSection.EDUCATION: [
        "education", "academic background", "academic history", "qualifications",
        "educational background", "academic qualifications", "studies"
    ],
    ResumeSection.SKILLS: [
        "skills", "technical skills", "competencies", "core competencies",
        "key skills", "professional skills", "expertise", "abilities"
    ],
    ResumeSection.PROJECTS: [
        "projects", "project experience", "key projects", "personal projects"
    ],
    ResumeSection.CERTIFICATIONS: [
        "certifications", "certificates", "professional certifications",
        "licenses", "accreditations"
    ],
    ResumeSection.LANGUAGES: [
        "languages", "language proficiency", "language skills"
    ],
    ResumeSection.SUMMARY: [
        "summary", "professional summary", "profile", "about me", "career objective",
        "objective", "career summary", "personal statement"
    ],
}

# Date Format Standardization
# ==========================

# Common date patterns in resumes (for extraction and standardization)
DATE_FORMAT_PATTERNS = [
    # Standard formats
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4} - (Present|Current|Now|\d{4})\b",
    r"\b\d{1,2}/\d{4} - (Present|Current|Now|\d{1,2}/\d{4})\b",
    r"\b\d{4} - (Present|Current|Now|\d{4})\b",
    # Additional formats from the text description
    r"\b\d{2}/\d{2}/\d{4}\b",  # DD/MM/YYYY
    r"\b\d{4}/\d{2}/\d{2}\b",  # YYYY/MM/DD
    r"\bFrom \d{4} (until|to) (today|present|now|current)\b",  # From YYYY until today
]

# Terms that represent "current" in date expressions
CURRENT_DATE_TERMS = [
    "present", "current", "now", "today", "ongoing"
]

# Standardized date format for internal storage (per the text description)
STANDARDIZED_DATE_FORMAT = "%Y-%m"  # YYYY-MM format

# Multilingual Support
# ===================

# Languages supported for resume analysis with their confidence scores
SUPPORTED_LANGUAGES = {
    "en": 0.97,  # English - 97% accuracy
    "fr": 0.96,  # French - 96% accuracy  
    "es": 0.95,  # Spanish - 95% accuracy
    "de": 0.94,  # German - 94% accuracy
    "zh": 0.93,  # Chinese - 93% accuracy
    "ar": 0.91,  # Arabic - 91% accuracy
    "ru": 0.92,  # Russian - 92% accuracy
    "pt": 0.94,  # Portuguese - 94% accuracy
    "hi": 0.90,  # Hindi - 90% accuracy
    "ja": 0.92,  # Japanese - 92% accuracy
}

# Skill Standardization
# ====================

# Example of skill term standardization mapping (as described in the text)
# This would be replaced by a more comprehensive database in production
SKILL_STANDARDIZATION_EXAMPLES = {
    "project management": ["managing projects", "project manager", "project lead", "leading project teams"],
    "python": ["python programming", "python development", "python coding", "python engineer"],
    "artificial intelligence": ["ai", "machine learning", "ml", "deep learning", "neural networks"],
    "data analysis": ["data analytics", "analyzing data", "data scientist", "data science"],
}

# OCR Configuration
# ================

# OCR configuration for different document types
OCR_CONFIGURATION = {
    "dpi": 300,  # Resolution for OCR processing
    "language_hints": ["en", "fr", "es", "de", "zh"],  # Languages to hint for OCR
    "enhance_contrast": True,  # Whether to enhance contrast for better OCR results
    "timeout_seconds": 120,  # Maximum time allowed for OCR processing
}

# Performance Metrics
# ==================

# Performance tracking metrics as described in the text
INITIAL_ACCURACY = {
    "name_extraction": 85.0,
    "education_extraction": 78.0,
    "skill_matching": 57.0,
    "date_detection": 75.0,
    "multilingual_processing": 55.0,
}

FINAL_ACCURACY = {
    "name_extraction": 98.0,
    "education_extraction": 98.0,
    "skill_matching": 96.0,
    "date_detection": 99.0,
    "multilingual_processing": 97.0,
}

# Progressive improvement milestones by month as mentioned in the text
MONTHLY_MILESTONES = {
    "jan": "Project initiation",
    "feb": "Sample collection and initial training",
    "mar": "Basic NER and OCR integration (75-78% accuracy)",
    "apr": "Semantic analysis improvements",
    "may": "Multilingual capability (80% accuracy)",
    "jun": "Date recognition algorithm (90% accuracy)",
    "jul": "Mid-year evaluation (90% overall accuracy)",
    "aug": "Advanced OCR techniques (90% accuracy for scanned resumes)",
    "sep": "UI refinements based on user feedback",
    "oct": "Full deployment (96-98% accuracy)",
    "nov": "Bug fixes and analytics improvements",
    "dec": "Project review and future planning"
}
