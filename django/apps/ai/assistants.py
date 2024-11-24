import contextlib
from collections import deque
from typing import ClassVar, List

from google.genai.types import ContentListUnion
from pydantic import BaseModel, ValidationError

from .google import GoogleServices


class Assistant[ResponseT: BaseModel]:
    assistant_slug: ClassVar[str]

    def __init__(self):
        self.service = self.get_service()

    def get_prompts(self, *args, **kwargs) -> ContentListUnion:
        raise NotImplementedError("This method should be overridden by subclasses.")

    def get_service(self) -> GoogleServices:
        return GoogleServices(self.assistant_slug)

    def should_pass(self, result: ResponseT):
        return True

    def response_builder(self, results: ResponseT, *, old_results: List[dict] = []):
        return self.service.message_to_json(results)

    def execute(self, *, is_json_marked=True, old_results: List) -> ResponseT | None:
        results = self.service.generate_text_content(self.get_prompts())

        return self.response_builder(results=results, old_results=old_results)


class AssistantPipeline:
    def __init__(self, *assistants: Assistant):
        self.assistants = assistants

    def run(self):
        results = deque()
        for assistant in self.assistants:
            with contextlib.suppress(ValidationError):
                result = assistant.execute(old_results=results.copy())
                results.append(result)
                if assistant.should_pass(result):
                    continue

            break

        return list(results)[-1]
