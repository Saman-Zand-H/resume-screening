import contextlib
import json
from typing import List

from ai.assistants import Assistant
from common.logging import get_logger
from config.settings.constants import Assistants
from google.genai import types as genai_types
from pydantic import ValidationError

from .typing.analysis import (
    VERIFICATION_METHOD_NAMES,
    AnalysisResponse,
    IsValid,
    OcrResponse,
)

logger = get_logger()


class DocumentValidationAssistant(Assistant[IsValid]):
    assistant_slug = Assistants.DOCUMENT_VALIDATION

    def build(self, file_model_id: int = None, verification_method_name: VERIFICATION_METHOD_NAMES = None, **kwargs):
        self.file_model_id = file_model_id
        self.verification_method_name = verification_method_name
        return self

    def get_prompts(self):
        file_part = self.service.get_file_part(self.file_model_id)
        text_part = genai_types.Part.from_text(
            text=json.dumps({"verification_method_name": self.verification_method_name})
        )

        return [file_part, text_part]

    def should_pass(self, result):
        return result.get("is_valid")

    def response_builder(self, results, **kwargs):
        response = super().response_builder(results)
        with contextlib.suppress(ValidationError):
            IsValid.model_validate(response)
            return response

        logger.warning(f"Validation for assistant {self.assistant_slug} failed. response: {response}")
        return IsValid(is_valid=False).model_dump_json()


class DocumentOcrAssistant(DocumentValidationAssistant, Assistant[OcrResponse]):
    assistant_slug = Assistants.OCR

    def get_prompts(self):
        if not (file_part := self.service.get_file_part(self.file_model_id)):
            return []

        return [
            file_part,
            genai_types.Part.from_text(text="extract text content"),
        ]

    def response_builder(self, results, **kwargs):
        response = super(DocumentValidationAssistant, self).response_builder(results=results)

        with contextlib.suppress(ValidationError):
            OcrResponse.model_validate(response)
            return response

        logger.warning(f"Validation for assistant {self.assistant_slug} failed. response: {response}")
        return OcrResponse(text_content="").model_dump_json()

    def should_pass(self, result):
        return len(result)


class DocumentDataAnalysisAssistant(DocumentValidationAssistant, Assistant[AnalysisResponse]):
    assistant_slug = Assistants.DOCUMENT_DATA_ANALYSIS

    def execute(self, *, is_json_marked=True, old_results):
        ocr_response = old_results[-1]
        with contextlib.suppress(ValidationError):
            OcrResponse.model_validate(ocr_response)
            prompt = [
                genai_types.Part.from_text(
                    text=json.dumps({"verification_method_name": self.verification_method_name} | ocr_response)
                )
            ]
            results = self.service.generate_text_content(prompt)
            return self.response_builder(results=results, old_results=old_results)

        return {}

    def response_builder(self, results, old_results: List[dict] = []):
        response = super(DocumentValidationAssistant, self).response_builder(results=results, old_results=old_results)
        if isinstance(response, dict):
            response["is_valid"] = True

        with contextlib.suppress(ValidationError):
            AnalysisResponse.model_validate(response)
            return response

        logger.warning(f"Validation for assistant {self.assistant_slug} failed. response: {response}")
        return {}
