"""
Resume Analysis settings module.

This module provides settings specific to the resume analysis functionality.
These settings can be overridden in the project's main settings.py file.
"""

from django.conf import settings

# Confidence threshold for resume analysis results
# Results with average confidence below this threshold will be rejected
RESUME_ANALYSIS_THRESHOLD = getattr(settings, 'RESUME_ANALYSIS_THRESHOLD', 0.7)

# Maximum resume text length to process (in characters)
MAX_RESUME_TEXT_LENGTH = getattr(settings, 'MAX_RESUME_TEXT_LENGTH', 50000)

# Maximum resume file size to process (in bytes, default 10MB)
MAX_RESUME_FILE_SIZE = getattr(settings, 'MAX_RESUME_FILE_SIZE', 10 * 1024 * 1024)

# Supported resume file types (mapped to FileType enum values)
SUPPORTED_RESUME_FILE_TYPES = getattr(settings, 'SUPPORTED_RESUME_FILE_TYPES', [
    'pdf', 'docx', 'doc', 'txt', 'rtf', 'image'
])

# Dictionary mapping skill categories to standardized industry names
SKILL_CATEGORY_MAPPING = getattr(settings, 'SKILL_CATEGORY_MAPPING', {
    'TECHNICAL': 'Technical Skills',
    'SOFT': 'Soft Skills',
    'LANGUAGE': 'Language Skills',
    'DOMAIN': 'Domain Expertise',
    'OTHER': 'Other Skills'
})

# List of required resume sections
REQUIRED_RESUME_SECTIONS = getattr(settings, 'REQUIRED_RESUME_SECTIONS', [
    'contact_info', 'education', 'work_experience', 'skills'
])

# Dictionary mapping language codes to language names
LANGUAGE_MAPPING = getattr(settings, 'LANGUAGE_MAPPING', {
    'en': 'English',
    'fr': 'French',
    'es': 'Spanish',
    'de': 'German',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ru': 'Russian',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'pt': 'Portuguese',
    'it': 'Italian'
}) 