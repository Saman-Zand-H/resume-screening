from itertools import chain
from operator import methodcaller
from typing import Any, ClassVar, Dict, List, Type

from flex_observer.types import FieldsObserver, InstanceType

from .score import Score


class ScoreObserver(FieldsObserver):
    scores: ClassVar[List[Type[Score]]]

    @classmethod
    def test_func(cls, instance: InstanceType):
        return True

    @classmethod
    def get_observed_fields(cls):
        return list(chain.from_iterable(map(methodcaller("get_observed_fields"), cls.get_scores())))

    @classmethod
    def get_scores(cls) -> List[Type[Score]]:
        return cls.scores

    @classmethod
    def calculate_score(cls, score: Type[Score], instance: InstanceType):
        pass

    @classmethod
    def scores_calculated(cls, instance: InstanceType, scores_dict: Dict[str, int]):
        pass

    @classmethod
    def get_calculate_params(cls, instance: InstanceType) -> Dict[str, Any]:
        return {}

    @classmethod
    def fields_changed(cls, changed_fields: List[str], instance: InstanceType, *args, **kwargs):
        if not changed_fields:
            return

        scores_dict = {}
        for score_class in cls.get_scores():
            if not score_class.test_func(instance):
                continue

            score = score_class()
            if changed_fields != ["*"] and not any(field in score.get_observed_fields() for field in changed_fields):
                continue

            scores_dict[score.slug] = score.calculate(**cls.get_calculate_params(instance))

        if scores_dict:
            cls.scores_calculated(instance, scores_dict)
