from typing import List, Type

from .app_settings import app_settings
from .utils import get_all_subclasses


class CategoryBase:
    @classmethod
    def get_all_categories(cls) -> List[Type["CategoryBase"]]:
        categories = get_all_subclasses(cls)
        members = set()

        for category in categories:
            for member in category:
                if member in members:
                    raise ValueError(f"Member {member} is already in a category")
                members.add(member)

        return categories

    @classmethod
    def validate_chosen_categories(cls):
        chosen_categories = app_settings.CATEGORIES
        all_categories = cls.get_all_categories()
        invalid_categories = filter(lambda category: category not in all_categories, chosen_categories)

        if invalid_categories and chosen_categories:
            raise ValueError(f"Invalid categories: {', '.join(map(str, invalid_categories))}")
