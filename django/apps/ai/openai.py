import io
import json
from io import BufferedReader
from typing import List, Optional, Tuple

from common.cache import Cache
from openai import OpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.threads import Message, Run
from openai.types.beta.vector_store import VectorStore

from django.conf import settings
from django.db.models import QuerySet
from django.http import HttpResponse

from .types import CachableVectorStore
from .utils import parse_json_markdown


class OpenAIService:
    assistant_id: str
    client: OpenAI

    def __init__(self, assistant_id: str):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.assistant_id = assistant_id

    @staticmethod
    def get_message_value(message: Message) -> str:
        return message.content[0].text.value

    def get_assistant(self) -> Assistant:
        return self.client.beta.assistants.retrieve(self.assistant_id)

    def get_run_result(self, run: Run) -> Optional[Message]:
        try:
            return self.client.beta.threads.messages.list(
                thread_id=run.thread_id,
                run_id=run.id,
                limit=1,
                order="desc",
            ).data[0]
        except IndexError:
            return None

    def vector_store_get_or_create(self, name: str) -> VectorStore:
        vector_store = self.client.beta.vector_stores.list()
        for v in vector_store:
            if v.name == name:
                return v
        return self.client.beta.vector_stores.create(name=name)

    def vector_store_files_add(self, vector_store: VectorStore, files: List[BufferedReader]):
        file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=files
        )
        return file_batch

    def vector_store_files_set(self, vector_store: VectorStore, files: List[BufferedReader]):
        current_files = self.client.beta.vector_stores.files.list(vector_store_id=vector_store.id)
        file_batch = self.vector_store_files_add(vector_store, files)
        if file_batch.status == "completed":
            self.files_delete([f.id for f in current_files])
        return file_batch

    def files_delete(self, files: List[str]):
        for f in files:
            self.client.files.delete(f)

    def vector_store_get_or_create_cache(
        self,
        cachable_vector_store: CachableVectorStore,
    ) -> Tuple[QuerySet, bool]:
        vector_store_qs, created = Cache.get_or_set_qs(cachable_vector_store.cache_key, cachable_vector_store.data_fn())
        if created:
            vs = self.vector_store_get_or_create(cachable_vector_store.id)
            file = io.BytesIO(json.dumps(list(vector_store_qs), separators=(",", ":")).encode())
            file.name = f"{cachable_vector_store.id}.json"
            self.vector_store_files_set(vs, [file])
        return vector_store_qs, created

    def assistant_vector_store_set(self, vector_store_ids: List[str]) -> bool:
        self.client.beta.assistants.update(
            assistant_id=self.assistant_id,
            tool_resources={"file_search": {"vector_store_ids": vector_store_ids}},
        )
        return True

    def assistant_vector_store_add(self, vector_store_ids: List[str]) -> bool:
        assistant = self.get_assistant()
        ids = set(assistant.tool_resources.file_search.vector_store_ids)
        new_ids = ids | set(vector_store_ids)
        if len(new_ids) != len(ids):
            self.assistant_vector_store_set(list(ids | new_ids))
            return True
        return False

    def send_text_to_assistant(self, text: str) -> Optional[Message]:
        thread = self.client.beta.threads.create(
            messages=[
                {"role": "user", "content": [{"type": "text", "text": text}]},
            ]
        )
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self.assistant_id,
        )
        return self.get_run_result(run)

    def assistant_vector_store_update_cache(self, cachable_vector_store: CachableVectorStore) -> bool:
        self.vector_store_get_or_create_cache(cachable_vector_store)
        return self.assistant_vector_store_add([self.vector_store_get_or_create(cachable_vector_store.id).id])

    def message_to_json(self, message: Message) -> dict:
        return parse_json_markdown(self.get_message_value(message))

