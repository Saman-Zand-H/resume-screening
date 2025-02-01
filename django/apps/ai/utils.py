import json
import re
import datetime
import logging
from typing import Dict, List, Optional, Set, Tuple, Union
import time
from pathlib import Path

# AI and ML libraries
import numpy as np
import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span
from transformers import (
    AutoTokenizer, 
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification,
    BertModel,
    GPT2LMHeadModel,
    pipeline
)
from sentence_transformers import SentenceTransformer, util
import torch
import langdetect
import dateparser
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from docx import Document
import textract
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from .constants import (
    CURRENT_DATE_TERMS,
    DATE_FORMAT_PATTERNS,
    FILE_TYPE_MAPPING,
    FINAL_ACCURACY,
    INITIAL_ACCURACY,
    NER_CONFIDENCE_THRESHOLD,
    NLP_MODELS,
    OCR_CONFIGURATION,
    SECTION_HEADERS,
    SKILL_MAPPING_CONFIDENCE,
    SKILL_STANDARDIZATION_EXAMPLES,
    STANDARDIZED_DATE_FORMAT,
    SUPPORTED_LANGUAGES,
    TARGET_ACCURACY,
)
from .types import (
    AccuracyMetric,
    Entity,
    EntityType,
    FileType,
    FileToTextResult,
    ResumeAnalysisResult,
    ResumeSection
)

# Setup logging
logger = logging.getLogger(__name__)

# Model caching
_NER_MODEL = None
_SECTION_CLASSIFIER = None
_SKILL_STANDARDIZER = None
_EMBEDDING_MODEL = None
_LANGUAGE_MODELS = {}


def parse_json_markdown(json_string: str) -> dict:
    json_string = json_string.strip()
    start_index = json_string.find("```json")
    end_index = json_string.find("```", start_index + len("```json"))

    if start_index != -1 and end_index != -1:
        extracted_content = json_string[start_index + len("```json") : end_index].strip()
        parsed = json.loads(extracted_content)
    elif start_index != -1 and end_index == -1 and json_string.endswith("``"):
        end_index = json_string.find("``", start_index + len("```json"))
        extracted_content = json_string[start_index + len("```json") : end_index].strip()
        parsed = json.loads(extracted_content)
    elif json_string.startswith("{"):
        parsed = json.loads(json_string)
    else:
        raise ValueError("Could not find JSON block in the output.")
    return parsed


# ================================================================
# Resume Processing Pipeline Functions
# ================================================================

def process_resume(file_path: Union[str, Path], file_mime_type: str) -> ResumeAnalysisResult:
    """
    Main function to process a resume file through the AI analysis pipeline.
    
    Args:
        file_path: Path to the resume file
        file_mime_type: MIME type of the file
        
    Returns:
        ResumeAnalysisResult containing extracted entities and sections
    """
    start_time = time.time()
    
    # Step 1: Extract text based on file type
    file_to_text_result = extract_text_from_file(file_path, file_mime_type)
    raw_text = file_to_text_result.text
    file_type = file_to_text_result.file_type
    
    # Step 2: Detect language
    language = detect_language(raw_text)
    
    # Step 3: Segment resume into sections
    sections = segment_resume_into_sections(raw_text, language)
    
    # Step 4: Extract entities (NER)
    entities = extract_entities(raw_text, sections, language)
    
    # Step 5: Standardize dates
    standardized_entities = standardize_dates(entities)
    
    # Step 6: Standardize skills
    standardized_entities = standardize_skills(standardized_entities, language)
    
    # Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    # Return the analysis result
    return ResumeAnalysisResult(
        entities=standardized_entities,
        sections=sections,
        raw_text=raw_text,
        language=language,
        file_type=file_type,
        processing_time_ms=processing_time_ms
    )


# ================================================================
# File Processing Functions
# ================================================================

def extract_text_from_file(file_path: Union[str, Path], file_mime_type: str) -> FileToTextResult:
    """
    Extract text from various file formats (PDF, DOCX, images, etc.)
    
    Args:
        file_path: Path to the file
        file_mime_type: MIME type of the file
        
    Returns:
        FileToTextResult with extracted text and metadata
    """
    # Determine file type from MIME type
    file_type = None
    for mime_prefix, file_type_enum in FILE_TYPE_MAPPING.items():
        if file_mime_type.startswith(mime_prefix):
            file_type = file_type_enum
            break
    
    if not file_type:
        # Default to OCR_REQUIRED if mime type not recognized
        file_type = FileType.OCR_REQUIRED
        
    # Extract text based on file type
    text = ""
    response = None
    
    try:
        if file_type == FileType.PDF:
            # PDF processing with text extraction and optional OCR
            text = extract_text_from_pdf(file_path)
            
        elif file_type == FileType.DOCX:
            # DOCX processing
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
        elif file_type == FileType.DOC:
            # DOC processing using textract
            text = textract.process(file_path).decode('utf-8', errors='replace')
            
        elif file_type == FileType.TXT:
            # Plain text processing
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                text = file.read()
                
        elif file_type == FileType.RTF:
            # RTF processing using textract
            text = textract.process(file_path).decode('utf-8', errors='replace')
            
        elif file_type == FileType.IMAGE or file_type == FileType.OCR_REQUIRED:
            # Image processing with OCR
            text, response = process_image_with_ocr(file_path)
            
        else:
            # Fallback to textract for unknown types
            text = textract.process(file_path).decode('utf-8', errors='replace')
        
    except Exception as e:
        logger.error(f"Error extracting text from file: {e}")
        # Fallback to OCR if text extraction fails
        file_type = FileType.OCR_REQUIRED
        text, response = process_image_with_ocr(file_path)
    
    return FileToTextResult(
        text=text,
        file_type=file_type,
        response=response
    )


def extract_text_from_pdf(file_path: Union[str, Path]) -> str:
    """
    Extract text from PDF files, with fallback to OCR if needed.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text
    """
    # Try PDF text extraction first (using PyPDF2 or pdfminer)
    try:
        import PyPDF2
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text() or ""
                
        # If text extraction yields very little text, use OCR as fallback
        if len(text.strip()) < 100:
            ocr_text, _ = process_pdf_with_ocr(file_path)
            return ocr_text
            
        return text
        
    except Exception as e:
        logger.warning(f"Error with PyPDF2 extraction, falling back to OCR: {e}")
        ocr_text, _ = process_pdf_with_ocr(file_path)
        return ocr_text


def process_pdf_with_ocr(file_path: Union[str, Path]) -> Tuple[str, Optional[Dict]]:
    """
    Process PDF with OCR by converting to images first.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Tuple of (extracted text, OCR response)
    """
    # Convert PDF to images
    try:
        images = convert_from_path(
            file_path,
            dpi=OCR_CONFIGURATION["dpi"]
        )
        
        full_text = ""
        for i, image in enumerate(images):
            # Process each page with OCR
            text = pytesseract.image_to_string(
                image, 
                lang="+".join(OCR_CONFIGURATION["language_hints"]),
                config='--psm 1'  # Page segmentation mode 1: Auto page segmentation with OSD
            )
            full_text += f"\n{text.strip()}"
            
        return full_text.strip(), None
        
    except Exception as e:
        logger.error(f"Error processing PDF with OCR: {e}")
        return "", None


def process_image_with_ocr(file_path: Union[str, Path]) -> Tuple[str, Optional[Dict]]:
    """
    Process image files with OCR to extract text.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Tuple of (extracted text, OCR response)
    """
    try:
        from PIL import Image, ImageEnhance
        
        # Open the image
        image = Image.open(file_path)
        
        # Enhance contrast for better OCR if configured
        if OCR_CONFIGURATION["enhance_contrast"]:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)  # Enhance contrast by factor of 2.0
        
        # Extract text using pytesseract
        text = pytesseract.image_to_string(
            image, 
            lang="+".join(OCR_CONFIGURATION["language_hints"]),
            config='--psm 1'  # Page segmentation mode 1: Auto page segmentation with OSD
        )
        
        return text.strip(), None
        
    except Exception as e:
        logger.error(f"Error processing image with OCR: {e}")
        return "", None


# ================================================================
# Language Detection Functions
# ================================================================

def detect_language(text: str) -> str:
    """
    Detect the language of the resume text.
    
    Args:
        text: The text to analyze
        
    Returns:
        ISO language code (e.g., 'en', 'fr')
    """
    try:
        # Use a larger sample of text for detection
        sample = text[:5000]  # Use first 5000 chars for detection
        lang = langdetect.detect(sample)
        
        # If detected language is supported, return it
        if lang in SUPPORTED_LANGUAGES:
            return lang
            
        # Default to English if not supported
        return "en"
        
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return "en"  # Default to English


# ================================================================
# Resume Section Detection and Segmentation
# ================================================================

def load_section_classifier():
    """Load and cache the section classifier model."""
    global _SECTION_CLASSIFIER
    
    if _SECTION_CLASSIFIER is None:
        try:
            # Load the Transformer model for section classification
            model_name = NLP_MODELS["section_classifier"]
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            _SECTION_CLASSIFIER = (tokenizer, model)
            logger.info(f"Loaded section classifier model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading section classifier: {e}")
            # Fallback to rule-based approach
            _SECTION_CLASSIFIER = None
            
    return _SECTION_CLASSIFIER


def segment_resume_into_sections(text: str, language: str = "en") -> Dict[ResumeSection, str]:
    """
    Segment a resume into different sections using NLP techniques.
    
    Args:
        text: The resume text
        language: Language code
        
    Returns:
        Dictionary mapping sections to their text content
    """
    # Try model-based classification if available
    section_classifier = load_section_classifier()
    
    if section_classifier is not None:
        try:
            return segment_with_model(text, section_classifier, language)
        except Exception as e:
            logger.warning(f"Model-based segmentation failed: {e}")
            # Fall back to rule-based approach
    
    # Rule-based section detection using regex and keyword matching
    return segment_with_rules(text, language)


def segment_with_model(text: str, classifier_tuple: Tuple, language: str) -> Dict[ResumeSection, str]:
    """
    Segment resume using the trained section classifier model.
    
    Args:
        text: The resume text
        classifier_tuple: Tuple containing (tokenizer, model)
        language: Language code
        
    Returns:
        Dictionary mapping sections to their text content
    """
    tokenizer, model = classifier_tuple
    sections = {}
    
    # Split text into paragraphs
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    
    # Process each paragraph to determine its section
    for paragraph in paragraphs:
        if len(paragraph.strip()) < 3:  # Skip very short paragraphs
            continue
            
        # Tokenize the paragraph
        inputs = tokenizer(paragraph, return_tensors="pt", truncation=True, max_length=512)
        
        # Get model predictions
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            predicted_class = logits.argmax(-1).item()
        
        # Map class index to section
        section_keys = list(ResumeSection)
        if predicted_class < len(section_keys):
            section = section_keys[predicted_class]
            
            # Append to existing section or create new
            if section in sections:
                sections[section] += "\n\n" + paragraph
            else:
                sections[section] = paragraph
    
    return sections


def segment_with_rules(text: str, language: str) -> Dict[ResumeSection, str]:
    """
    Segment resume using rule-based approach with regex and keywords.
    
    Args:
        text: The resume text
        language: Language code
        
    Returns:
        Dictionary mapping sections to their text content
    """
    sections = {}
    current_section = None
    section_text = ""
    
    # Split text into lines
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Check if this line is a section header
        found_section = None
        for section, headers in SECTION_HEADERS.items():
            # Check for headers (case-insensitive)
            line_lower = line.lower()
            for header in headers:
                if header in line_lower or line_lower == header:
                    found_section = section
                    break
            if found_section:
                break
        
        if found_section:
            # Save previous section if it exists
            if current_section and section_text:
                sections[current_section] = section_text.strip()
            
            # Start new section
            current_section = found_section
            section_text = ""
        elif current_section:
            # Add line to current section
            section_text += line + "\n"
    
    # Add the last section
    if current_section and section_text:
        sections[current_section] = section_text.strip()
    
    # If no sections were found, create a default entry with all text
    if not sections:
        sections[ResumeSection.WORK_EXPERIENCE] = text
    
    return sections


# ================================================================
# Named Entity Recognition (NER) Functions
# ================================================================

def load_ner_model(language: str = "en"):
    """Load and cache NER model for the specified language."""
    global _NER_MODEL, _LANGUAGE_MODELS
    
    if language in _LANGUAGE_MODELS:
        return _LANGUAGE_MODELS[language]
    
    try:
        # For English, use our custom model
        if language == "en":
            model_name = NLP_MODELS["resume_ner"]
            # Use Hugging Face pipeline for token classification
            _LANGUAGE_MODELS[language] = pipeline(
                "token-classification", 
                model=model_name,
                aggregation_strategy="simple"
            )
        # For other languages, use spaCy models
        else:
            # Map language code to spaCy model
            lang_model_map = {
                "fr": "fr_core_news_lg",
                "es": "es_core_news_lg",
                "de": "de_core_news_lg",
                "zh": "zh_core_web_lg",
                "pt": "pt_core_news_lg",
            }
            
            # If language supported by spaCy, use it
            if language in lang_model_map:
                import spacy
                model_name = lang_model_map[language]
                _LANGUAGE_MODELS[language] = spacy.load(model_name)
            # Otherwise use multilingual model
            else:
                model_name = NLP_MODELS["multilingual"]
                _LANGUAGE_MODELS[language] = pipeline(
                    "token-classification", 
                    model=model_name,
                    aggregation_strategy="simple"
                )
                
        logger.info(f"Loaded NER model for language '{language}': {model_name}")
        return _LANGUAGE_MODELS[language]
        
    except Exception as e:
        logger.error(f"Error loading NER model for language '{language}': {e}")
        # Fall back to English model
        if language != "en" and "en" in _LANGUAGE_MODELS:
            logger.warning(f"Falling back to English NER model for language '{language}'")
            return _LANGUAGE_MODELS["en"]
        else:
            # Last resort: load spaCy's en_core_web_sm
            import spacy
            _LANGUAGE_MODELS["en"] = spacy.load("en_core_web_sm")
            return _LANGUAGE_MODELS["en"]


def extract_entities(text: str, sections: Dict[ResumeSection, str], language: str = "en") -> List[Entity]:
    """
    Extract entities from resume text using NER.
    
    Args:
        text: The resume text
        sections: Dictionary of resume sections
        language: Language code
        
    Returns:
        List of Entity objects
    """
    entities = []
    
    # Load appropriate NER model
    ner_model = load_ner_model(language)
    
    # Process different sections with appropriate entity focus
    for section, section_text in sections.items():
        # Skip empty sections
        if not section_text.strip():
            continue
            
        section_entities = []
        
        # Use appropriate NER approach based on the model type
        if isinstance(ner_model, spacy.language.Language):
            # Process with spaCy
            section_entities = extract_entities_with_spacy(ner_model, section_text, section)
        else:
            # Process with Hugging Face transformers pipeline
            section_entities = extract_entities_with_transformers(ner_model, section_text, section)
            
        # Add entities from this section
        entities.extend(section_entities)
        
    # Extract additional entities from the full text (e.g., email, phone, etc.)
    supplementary_entities = extract_supplementary_entities(text)
    entities.extend(supplementary_entities)
    
    return entities


def extract_entities_with_spacy(nlp_model: Language, text: str, section: ResumeSection) -> List[Entity]:
    """
    Extract entities using spaCy NER.
    
    Args:
        nlp_model: Loaded spaCy model
        text: Text to analyze
        section: Current resume section
        
    Returns:
        List of Entity objects
    """
    entities = []
    doc = nlp_model(text)
    
    # Map spaCy entity labels to our EntityType
    label_map = {
        "PERSON": EntityType.NAME,
        "ORG": EntityType.COMPANY,
        "DATE": EntityType.DATE,
        "GPE": EntityType.LOCATION,
        "EMAIL": EntityType.EMAIL,
        "PHONE": EntityType.PHONE,
        "URL": EntityType.URL,
        "SKILL": EntityType.SKILL,  # Custom entity type if available
    }
    
    # Extract recognized entities
    for ent in doc.ents:
        # Map spaCy label to our entity type
        entity_type = label_map.get(ent.label_)
        
        # Handle special cases based on section context
        if entity_type is None:
            # Try to infer entity type from section context
            if section == ResumeSection.EDUCATION and ent.label_ in ["ORG", "PRODUCT"]:
                entity_type = EntityType.EDUCATION
            elif section == ResumeSection.WORK_EXPERIENCE and ent.label_ == "ORG":
                entity_type = EntityType.COMPANY
            elif section == ResumeSection.SKILLS:
                entity_type = EntityType.SKILL
            elif section == ResumeSection.CERTIFICATIONS:
                entity_type = EntityType.CERTIFICATION
            else:
                # Skip if we can't map the entity type
                continue
                
        # Create and add the entity
        entity = Entity(
            text=ent.text,
            entity_type=entity_type,
            confidence=0.9,  # spaCy doesn't provide confidence scores, using default
            section=section,
            start_index=ent.start_char,
            end_index=ent.end_char
        )
        entities.append(entity)
    
    return entities


def extract_entities_with_transformers(ner_pipeline, text: str, section: ResumeSection) -> List[Entity]:
    """
    Extract entities using Hugging Face transformers NER pipeline.
    
    Args:
        ner_pipeline: Loaded transformers NER pipeline
        text: Text to analyze
        section: Current resume section
        
    Returns:
        List of Entity objects
    """
    entities = []
    
    # Process text with the NER pipeline
    ner_results = ner_pipeline(text)
    
    # Map Hugging Face entity labels to our EntityType
    # Assuming the model is trained on resume-specific entity types
    label_map = {
        "PERSON": EntityType.NAME,
        "ORGANIZATION": EntityType.COMPANY,
        "DATE": EntityType.DATE,
        "LOCATION": EntityType.LOCATION,
        "EMAIL": EntityType.EMAIL,
        "PHONE": EntityType.PHONE,
        "URL": EntityType.URL,
        "JOB_TITLE": EntityType.JOB_TITLE,
        "EDUCATION": EntityType.EDUCATION,
        "SKILL": EntityType.SKILL,
        "CERTIFICATION": EntityType.CERTIFICATION,
        "PROJECT": EntityType.PROJECT,
    }
    
    # Extract recognized entities
    for entity_result in ner_results:
        # Map label to our entity type
        label = entity_result["entity_group"]
        entity_type = label_map.get(label)
        
        # Handle special cases based on section context
        if entity_type is None:
            # Try to determine entity type from section and label
            if section == ResumeSection.EDUCATION and label in ["ORG", "MISC"]:
                entity_type = EntityType.EDUCATION
            elif section == ResumeSection.WORK_EXPERIENCE and label in ["ORG", "MISC"]:
                entity_type = EntityType.COMPANY
            elif section == ResumeSection.SKILLS and label in ["MISC", "SKILL"]:
                entity_type = EntityType.SKILL
            elif section == ResumeSection.CERTIFICATIONS and label in ["MISC", "CREDENTIAL"]:
                entity_type = EntityType.CERTIFICATION
            else:
                # Skip if we can't map the entity type
                continue
                
        # Skip entities with confidence lower than threshold
        if entity_result["score"] < NER_CONFIDENCE_THRESHOLD:
            continue
                
        # Create and add the entity
        entity = Entity(
            text=entity_result["word"],
            entity_type=entity_type,
            confidence=entity_result["score"],
            section=section,
            start_index=entity_result["start"],
            end_index=entity_result["end"]
        )
        entities.append(entity)
    
    return entities


def extract_supplementary_entities(text: str) -> List[Entity]:
    """
    Extract additional entities like emails, phone numbers, URLs using regex patterns.
    
    Args:
        text: The full resume text
        
    Returns:
        List of supplementary entities
    """
    entities = []
    
    # Email pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.finditer(email_pattern, text)
    for match in emails:
        entities.append(Entity(
            text=match.group(),
            entity_type=EntityType.EMAIL,
            confidence=0.99,  # High confidence for regex patterns
            start_index=match.start(),
            end_index=match.end()
        ))
    
    # Phone pattern (simplified, should be made more robust)
    phone_pattern = r'\+?[0-9]{1,4}?[-.\s]?\(?\d{1,4}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
    phones = re.finditer(phone_pattern, text)
    for match in phones:
        entities.append(Entity(
            text=match.group(),
            entity_type=EntityType.PHONE,
            confidence=0.95,
            start_index=match.start(),
            end_index=match.end()
        ))
    
    # URL pattern
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    urls = re.finditer(url_pattern, text)
    for match in urls:
        entities.append(Entity(
            text=match.group(),
            entity_type=EntityType.URL,
            confidence=0.99,
            start_index=match.start(),
            end_index=match.end()
        ))
    
    return entities


# ================================================================
# Date Standardization Functions
# ================================================================

def standardize_dates(entities: List[Entity]) -> List[Entity]:
    """
    Standardize date entities into a consistent format.
    
    Args:
        entities: List of extracted entities
        
    Returns:
        List of entities with standardized dates
    """
    standardized_entities = []
    
    for entity in entities:
        if entity.entity_type == EntityType.DATE:
            # Try to parse the date
            standardized_date = standardize_date_format(entity.text)
            if standardized_date:
                entity.normalized_value = standardized_date
                
        standardized_entities.append(entity)
    
    return standardized_entities


def standardize_date_format(date_text: str) -> Optional[str]:
    """
    Convert various date formats to a standardized format.
    
    Args:
        date_text: Date text to standardize
        
    Returns:
        Standardized date string (YYYY-MM) or None if parsing fails
    """
    # Handle "Present", "Current", etc.
    for term in CURRENT_DATE_TERMS:
        if term.lower() in date_text.lower():
            # Replace with current date
            today = datetime.datetime.now()
            date_text = date_text.lower().replace(term.lower(), today.strftime("%Y-%m"))
    
    # Try to parse with dateparser
    try:
        parsed_date = dateparser.parse(date_text)
        if parsed_date:
            return parsed_date.strftime(STANDARDIZED_DATE_FORMAT)
    except Exception as e:
        logger.warning(f"Date parsing failed with dateparser: {e}")
    
    # Fallback: Use regex patterns for common formats
    for pattern in DATE_FORMAT_PATTERNS:
        match = re.search(pattern, date_text)
        if match:
            try:
                # Extract just the year and month if possible
                date_parts = match.group().split()
                if len(date_parts) >= 2:
                    # Try to extract year and month
                    for part in date_parts:
                        # Check if part is a year
                        if re.match(r'\d{4}', part):
                            year = part
                            # Find month if available
                            month_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*', date_text)
                            if month_match:
                                month_str = month_match.group()[:3]
                                month_to_num = {
                                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                                }
                                month = month_to_num.get(month_str, '01')
                                return f"{year}-{month}"
                            return f"{year}-01"  # Default to January if month not found
            except Exception as e:
                logger.warning(f"Regex date parsing failed: {e}")
    
    # Return None if all parsing methods fail
    return None


# ================================================================
# Skill Standardization Functions
# ================================================================

def load_skill_standardizer():
    """Load and cache the skill standardization model."""
    global _SKILL_STANDARDIZER, _EMBEDDING_MODEL
    
    if _SKILL_STANDARDIZER is None:
        try:
            # Load the model for skill standardization
            model_name = NLP_MODELS["skill_standardization"]
            _EMBEDDING_MODEL = SentenceTransformer(model_name)
            
            # Prepare skill standardization database
            _SKILL_STANDARDIZER = {}
            
            # Generate embeddings for standard skill terms
            for standard_skill, variations in SKILL_STANDARDIZATION_EXAMPLES.items():
                # Create a mapping from variations to the standard term
                _SKILL_STANDARDIZER[standard_skill] = standard_skill
                for variation in variations:
                    _SKILL_STANDARDIZER[variation.lower()] = standard_skill
            
            logger.info(f"Loaded skill standardization model: {model_name}")
            
        except Exception as e:
            logger.error(f"Error loading skill standardizer: {e}")
            # Fallback to simple dictionary-based approach
            _SKILL_STANDARDIZER = {
                variation.lower(): standard
                for standard, variations in SKILL_STANDARDIZATION_EXAMPLES.items()
                for variation in variations
            }
    
    return _SKILL_STANDARDIZER, _EMBEDDING_MODEL


def standardize_skills(entities: List[Entity], language: str = "en") -> List[Entity]:
    """
    Standardize skill entities to normalized terms.
    
    Args:
        entities: List of extracted entities
        language: Language code
        
    Returns:
        List of entities with standardized skills
    """
    # Load skill standardizer
    skill_map, embedding_model = load_skill_standardizer()
    
    for entity in entities:
        if entity.entity_type == EntityType.SKILL:
            skill_text = entity.text.lower()
            
            # First check if the skill is in our mapping dictionary
            if skill_text in skill_map:
                entity.normalized_value = skill_map[skill_text]
                continue
                
            # If not found in the dictionary, use semantic similarity
            if embedding_model is not None:
                try:
                    # Get embedding for the skill text
                    skill_embedding = embedding_model.encode(skill_text, convert_to_tensor=True)
                    
                    # Find most similar standard skill term
                    max_similarity = -1
                    best_match = None
                    
                    for standard_skill in SKILL_STANDARDIZATION_EXAMPLES.keys():
                        # Get embedding for standard skill
                        standard_embedding = embedding_model.encode(standard_skill, convert_to_tensor=True)
                        
                        # Calculate cosine similarity
                        similarity = util.pytorch_cos_sim(skill_embedding, standard_embedding).item()
                        
                        if similarity > max_similarity and similarity > SKILL_MAPPING_CONFIDENCE:
                            max_similarity = similarity
                            best_match = standard_skill
                    
                    if best_match:
                        entity.normalized_value = best_match
                        # Also update confidence based on similarity
                        entity.confidence *= max_similarity
                    else:
                        # Keep original if no good match found
                        entity.normalized_value = entity.text
                        
                except Exception as e:
                    logger.warning(f"Skill standardization with embedding model failed: {e}")
                    entity.normalized_value = entity.text
            else:
                # Fallback if embedding model not available
                entity.normalized_value = entity.text
    
    return entities


# ================================================================
# Accuracy Measurement Functions
# ================================================================

def calculate_accuracy_metrics(predicted_entities: List[Entity], 
                              ground_truth_entities: List[Entity]) -> Dict[EntityType, AccuracyMetric]:
    """
    Calculate accuracy metrics by comparing predicted entities to ground truth.
    
    Args:
        predicted_entities: Entities extracted by the system
        ground_truth_entities: Manually annotated entities for comparison
        
    Returns:
        Dictionary of accuracy metrics by entity type
    """
    # Initialize metrics for each entity type
    metrics = {entity_type: AccuracyMetric(entity_type=entity_type) 
               for entity_type in EntityType}
    
    # Count correct predictions for each entity type
    for true_entity in ground_truth_entities:
        entity_type = true_entity.entity_type
        metrics[entity_type].total_count += 1
        
        # Check if this entity was correctly identified
        for pred_entity in predicted_entities:
            if (pred_entity.entity_type == entity_type and
                pred_entity.text.lower() == true_entity.text.lower()):
                metrics[entity_type].correct_count += 1
                break
    
    return metrics
