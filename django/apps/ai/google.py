from typing import Optional, Union

import magic
from google.cloud import vision

from .constants import FILE_TYPE_MAPPING, FileType
from .types import FileToTextResult


class GoogleServices:
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
