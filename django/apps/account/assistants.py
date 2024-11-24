import contextlib
import json
from typing import List

from ai.assistants import Assistant
from common.logging import get_logger
from common.models import LanguageProficiencySkill, LanguageProficiencyTest
from common.utils import fields_join
from config.settings.constants import Assistants
from google.genai import types as genai_types
from pydantic import ValidationError

from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import F, OuterRef, Subquery
from django.db.models.functions import JSONObject

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
                ),
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


class LanguageCertificateAnalysisAssistant(DocumentDataAnalysisAssistant, Assistant[AnalysisResponse]):
    assistant_slug = Assistants.LANGUAGE_CERTIFICATE_ANALYSIS

    def execute(self, *, is_json_marked=True, old_results):
        ocr_response = old_results[-1]
        with contextlib.suppress(ValidationError):
            OcrResponse.model_validate(ocr_response)

            skills_subq = Subquery(
                LanguageProficiencySkill.objects.filter(
                    **{
                        fields_join(
                            LanguageProficiencySkill.test, LanguageProficiencyTest._meta.pk.get_attname()
                        ): OuterRef(LanguageProficiencyTest._meta.pk.get_attname())
                    }
                ).values_list(
                    JSONObject(
                        **{
                            fields_join(LanguageProficiencySkill.skill_name): F(
                                fields_join(LanguageProficiencySkill.skill_name)
                            ),
                            fields_join(LanguageProficiencySkill._meta.pk.get_attname()): F(
                                fields_join(LanguageProficiencySkill._meta.pk.get_attname())
                            ),
                        }
                    ),
                    flat=True,
                )
            )

            language_tests_data = LanguageProficiencyTest.objects.prefetch_related(
                LanguageProficiencySkill.test.field.related_query_name()
            ).values(
                LanguageProficiencyTest._meta.pk.get_attname(),
                fields_join(LanguageProficiencyTest.title),
                fields_join(LanguageProficiencyTest.languages),
                skills_data=ArraySubquery(skills_subq),
            )

            prompt = [
                genai_types.Part.from_text(
                    text=json.dumps({"verification_method_name": self.verification_method_name} | ocr_response)
                ),
                genai_types.Part.from_text(text="\n\nTHE FOLLOWING ARE THE DATA\n\n"),
                genai_types.Part.from_text(text=json.dumps(language_tests_data)),
            ]

            results = self.service.generate_text_content(prompt)
            return self.response_builder(results=results, old_results=old_results)

        return {}
