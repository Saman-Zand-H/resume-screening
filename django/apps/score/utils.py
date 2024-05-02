from typing import Type

from .types import Score, ScorePack, ScoreRegistry


def register_score(cls: Type["Score"]):
    if not hasattr(cls, "slug") or not cls.slug:
        raise ValueError(f"Score subclass must define a 'slug' in '{cls.__name__}'")
    ScoreRegistry.register_score(cls)
    return cls


def register_pack(cls: Type["ScorePack"]):
    if not hasattr(cls, "slug") or not cls.slug:
        raise ValueError("ScorePack subclass must define a 'slug'")
    ScoreRegistry.register_pack(cls)
    return cls
