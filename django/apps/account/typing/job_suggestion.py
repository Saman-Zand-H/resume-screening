from typing import List

from pydantic import BaseModel


class JobSuggestionWords(BaseModel):
    keywords: List[str]
    clue_words: List[str]
