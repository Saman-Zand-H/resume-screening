"""
AI-Based Resume Analysis System

This module provides functionality for analyzing resumes using advanced AI techniques.
It processes resumes in various formats (PDF, DOCX, images) and extracts structured information
like personal details, education, work experience, skills, and certifications.

Key features:
- Named Entity Recognition (NER) for extracting key information
- OCR for processing scanned resumes and images
- Multilingual processing capabilities
- Date and skill standardization
- Resume section detection and segmentation
"""

default_app_config = "django.apps.ai.apps.AIConfig"

# Version
__version__ = "1.0.0"
