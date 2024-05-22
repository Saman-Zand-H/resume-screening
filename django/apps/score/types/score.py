from functools import partial, wraps
from typing import Callable, ClassVar, Dict, List, Literal, Type

from account.models import Profile, User
from common.utils import get_all_subclasses
from pydantic import BaseModel, Field, PrivateAttr

from django.db.models import Model
from django.db.models.signals import m2m_changed, pre_save
from django.dispatch import receiver

M2mChangedActions = Literal["pre_add", "post_add", "pre_remove", "post_remove", "pre_clear", "post_clear"]


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
    _model_: ClassVar[Type] = PrivateAttr()
    model_config = {"ignored_types": (Type,)}

    slug: ClassVar[str]
    observed_fields: ClassVar[List[str]] = Field(default_factory=list)

    @classmethod
    def get_observed_fields(cls) -> List[str]:
        return cls.observed_fields

    def calculate(self, user) -> int:
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


class ScoreObserver[T: Model](BaseModel):
    _model_: ClassVar[T] = PrivateAttr()
    scores: ClassVar[List[Type[Score]]]

    @classmethod
    def get_user(cls, instance: T) -> User:
        return getattr(instance, "user", instance)

    @classmethod
    def test_func(cls, instance: T) -> bool:
        return True

    @classmethod
    def get_scores[S: Score](cls) -> List[S]:
        return getattr(cls, "scores", [cls])

    @classmethod
    def find_changed_fields(cls, old_instance: T, new_instance: T, observed_fields: List[str]) -> List[str]:
        has_field_changed = lambda field: getattr(old_instance, field) != getattr(new_instance, field)  # noqa

        return [field for field in observed_fields if has_field_changed(field)]

    @classmethod
    def observe_handler[S: Score](cls, scores: S, old_instance: T, new_instance: T):
        if not cls.test_func(new_instance):
            return

        profile = (user := cls.get_user(new_instance)).get_profile()

        if not (updated_scores := cls.calculate_scores(scores, old_instance, new_instance, user)):
            return

        cls.update_profile_scores(profile, updated_scores)

    @classmethod
    def get_through_models(
        cls,
    ):
        return [
            field.remote_field.through
            for score in cls.get_scores()
            for field_name in score.get_observed_fields()
            if (field := cls._model_._meta.get_field(field_name)).many_to_many
        ]

    @classmethod
    def calculate_scores[S: Score](
        cls, scores: List[S], old_instance: T, new_instance: T, user: User
    ) -> Dict[str, int]:
        updated_scores = {}
        for score_cls in scores:
            score = score_cls()
            breakpoint()
            observed_fields = score.get_observed_fields()

            if not cls.find_changed_fields(old_instance, new_instance, observed_fields) and old_instance:
                continue

            updated_scores[score.slug] = score.calculate(user)

        if not updated_scores:
            return

        return updated_scores

    @staticmethod
    def update_profile_scores(profile: Profile, updated_scores: Dict[str, int]):
        profile.scores.update(updated_scores)
        profile.score = sum(profile.scores.values())
        Profile.objects.filter(pk=profile.pk).update(score=profile.score, scores=profile.scores)

    @classmethod
    def observe[S: Score](cls, scores: List[S], instance: T, sender: Type[T], *args, **kwargs):
        old_instance = sender.objects.filter(pk=instance.pk).first()
        cls.observe_handler(scores, old_instance, instance)

    @classmethod
    def pre_add_observer(cls, score_observer: Callable):
        @wraps(score_observer.observe)
        def wrapper(action: M2mChangedActions, *args, **kwargs):
            breakpoint()
            if action != "pre_add":
                return

            return score_observer.observe(*args, **kwargs, scores=[score_observer])

        return wrapper

    @classmethod
    def register_signals(cls):
        for score_observer in get_all_subclasses(cls):
            receiver(pre_save, sender=score_observer._model_)(partial(score_observer.observe, scores=cls.get_scores()))
            for through_model in score_observer.get_through_models():
                receiver(m2m_changed, sender=through_model)(cls.pre_add_observer(score_observer))
