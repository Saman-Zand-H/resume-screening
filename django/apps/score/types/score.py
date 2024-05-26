from typing import ClassVar, Dict, List, Type

from account.models import User
from pydantic import BaseModel, Field, PrivateAttr


class ScoreRegistry:
    scores: Dict[str, Type["Score"]] = {}
    packs: Dict[str, Type["ScorePack"]] = {}

    @classmethod
    def register_score(cls, score_cls: Type["Score"]):
        if score_cls.slug in cls.scores:
            raise ValueError(f"Score '{score_cls.slug}' is already registered")
        cls.scores[score_cls.slug] = score_cls

    @classmethod
    def register_pack(cls, pack_cls: Type["ScorePack"]):
        if pack_cls.slug in cls.packs:
            raise ValueError(f"ScorePack '{pack_cls.slug}' is already registered")
        cls.packs[pack_cls.slug] = pack_cls


class Score(BaseModel):
    _observed_model: ClassVar[Type] = PrivateAttr()
    model_config = {"ignored_types": (Type,)}

    slug: ClassVar[str]
    observed_fields: ClassVar[List[str]] = Field(default_factory=list)

    @classmethod
    def test_func(cls, instance):
        return True

    @classmethod
    def get_observed_fields(cls) -> List[str]:
        return cls.observed_fields

    def calculate(self, *args, **kwargs) -> int:
        raise NotImplementedError(f"Subclasses must implement 'calculate' in '{self.__class__.__name__}'")


class ExistingScore(Score):
    score: ClassVar[int]

    def get_value(self, user) -> int:
        raise NotImplementedError("Subclasses must implement 'get_value'")

    def calculate(self, user) -> int:
        return self.score if self.get_value(user) else 0


class ScorePack(BaseModel):
    slug: ClassVar[str]
    scores: ClassVar[List[Type[Score]]]

    @classmethod
    def calculate(cls, user: User) -> Dict[str, int]:
        return {score.slug: score().calculate(user) for score in cls.scores}

    @classmethod
    def calculate_total(cls, user) -> int:
        return sum(cls.calculate(user).values())
