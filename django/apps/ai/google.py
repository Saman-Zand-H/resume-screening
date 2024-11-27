from typing import Optional, Union

import magic
from common.utils import get_file_model_mimetype
from flex_blob.models import FileModel
from google import genai
from google.cloud import vision
from google.genai import types as genai_types

from django.conf import settings

from .constants import FILE_TYPE_MAPPING, FileType
from .models import VertexAIModel
from .types import FileToTextResult
from .utils import parse_json_markdown


class GoogleServices:
    client: genai.Client

    def __init__(self, model_slug: str):
        if not (instance := VertexAIModel.objects.filter(**{VertexAIModel.slug.field.name: model_slug}).first()):
            raise ValueError("Model not found")

        self.instance = instance
        self.client = genai.Client(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION,
            vertexai=True,
        )

    def get_file_part(self, file_model_id: int) -> genai_types.ContentUnion:
        if not (file_model := FileModel.objects.filter(pk=file_model_id).first()):
            return []

        mime_type = get_file_model_mimetype(file_model)
        with file_model.file.open("rb") as file:
            file_bytes = file.read()

        return genai_types.Part.from_bytes(
            data=file_bytes,
            mime_type=mime_type,
        )

    def generate_content(self, contents: genai_types.ContentListUnion):
        return self.client.models.generate_content(
            model=self.instance.model_name,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                temperature=self.instance.temperature,
                max_output_tokens=self.instance.max_tokens,
                system_instruction=self.instance.instruction,
            ),
        )

    def generate_text_content(self, contents: genai_types.ContentListUnion) -> str:
        return self.generate_content(contents).text

    @staticmethod
    def message_to_json(results: str):
        return parse_json_markdown(results)

    @classmethod
    def get_vision_client(cls) -> vision.ImageAnnotatorClient:
        return vision.ImageAnnotatorClient()

    @classmethod
    def file_vision(
        cls, file_bytes: bytes, file_type: FileType
    ) -> Optional[Union[vision.AnnotateImageResponse, vision.AnnotateFileResponse]]:
        client = cls.get_vision_client()
        match file_type:
            case FileType.IMAGE:
                return client.text_detection(image=vision.Image(content=file_bytes))
            case FileType.PDF:
                file_request = vision.AnnotateFileRequest(
                    features=[vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)],
                    input_config=vision.InputConfig(content=file_bytes, mime_type="application/pdf"),
                )
                responses = client.batch_annotate_files(requests=[file_request]).responses
                if responses:
                    return responses[0]
                return None
            case _:
                raise NotImplementedError("File type not supported")

    @classmethod
    def detect_file_type(cls, file_bytes: bytes) -> Optional[FileType]:
        mime_type = magic.from_buffer(file_bytes, mime=True)
        return next((mime for file_type, mime in FILE_TYPE_MAPPING.items() if file_type in mime_type), None)

    @classmethod
    def file_to_text(cls, file_bytes: bytes) -> Optional[FileToTextResult]:
        if not (file_type := cls.detect_file_type(file_bytes)):
            raise ValueError("Invalid file type")
        response = cls.file_vision(file_bytes, file_type)
        if not response:
            return None
        text = None
        match file_type:
            case FileType.IMAGE:
                text = response.text_annotations[0].description
            case FileType.PDF:
                text = "\n".join([page.full_text_annotation.text for page in response.responses])
        return FileToTextResult(text=text, file_type=file_type, response=response)
