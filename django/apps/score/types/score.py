from typing import ClassVar, Dict, List, Type

from account.models import Profile, User
from common.utils import get_all_subclasses
from pydantic import BaseModel, Field, PrivateAttr

from django.db.models import Model
from django.db.models.signals import pre_save
from django.dispatch import receiver


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

    def get_observed_fields(self) -> List[str]:
        return self.observed_fields

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
        def get_field_value(instance, field):
            return getattr(instance, field, None)

        def is_m2m_field(value):
            return hasattr(value, "all") and callable(value.all)

        def get_m2m_set(value):
            return set(value.all()) if value else set()

        def has_field_changed(old_value, new_value):
            if is_m2m_field(old_value):
                return get_m2m_set(old_value) != get_m2m_set(new_value)
            return old_value != new_value

        changed_fields = [
            field
            for field in observed_fields
            if has_field_changed(get_field_value(old_instance, field), get_field_value(new_instance, field))
        ]
        return changed_fields

    @classmethod
    def observe_handler(cls, old_instance: T, new_instance: T):
        if not cls.test_func(new_instance):
            return

        profile = (user := cls.get_user(new_instance)).get_profile()

        if not (updated_scores := cls.calculate_scores(old_instance, new_instance, user)):
            return

        cls.update_profile_scores(profile, updated_scores)

    @classmethod
    def calculate_scores(cls, old_instance: T, new_instance: T, user: "User") -> Dict[str, int]:
        updated_scores = {}
        for score_cls in cls.get_scores():
            score: Score = score_cls()
            observed_fields = score.get_observed_fields()

            if not cls.find_changed_fields(old_instance, new_instance, observed_fields):
                continue

            updated_scores[score.slug] = score.calculate(user)

        if not updated_scores:
            return

        return updated_scores

    @staticmethod
    def update_profile_scores(profile: Profile, updated_scores: Dict[str, int]):
        scores = profile.scores or {}
        scores.update(updated_scores)
        score = sum(scores.values())
        profile.score = score
        Profile.objects.filter(pk=profile.pk).update(scores=scores, score=score)

    @classmethod
    def observe(cls, instance: T, sender: Type[T], *args, **kwargs):
        try:
            if not (old_instance := sender.objects.get(pk=instance.pk)):
                return
        except sender.DoesNotExist:
            return
        cls.observe_handler(old_instance, instance)

    @classmethod
    def register_signals(cls):
        for score_observer in get_all_subclasses(cls):
            receiver(pre_save, sender=score_observer._model_)(score_observer.observe)
