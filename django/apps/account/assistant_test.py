import operator
from functools import reduce
from itertools import chain
from typing import List

from common.db_functions import Sigmoid
from pydantic import BaseModel, RootModel

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import (
    Case,
    ExpressionWrapper,
    F,
    FloatField,
    Func,
    Max,
    Q,
    Subquery,
    TextField,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce

from .models import User


class KeywordClueWord(BaseModel):
    keywords: List[List[str]]
    clue_words: List[str]


class WeightBasedItem(BaseModel):
    keyword: str
    weight: float


WeightBasedItems = RootModel[List[WeightBasedItem]]


class TextSimilarity(Func):
    function = "SIMILARITY"
    template = "%(function)s(%(expressions)s)"
    output_field = FloatField()

    def __init__(self, expression1, expression2, **extra):
        expressions = [Cast(expression1, TextField()), Cast(expression2, TextField())]
        super().__init__(*expressions, **extra)


def vector_search(search_terms: KeywordClueWord, *, top_r=0.5, steepness=1.0, midpoint=0.0):
    fields = [
        "profile__interested_jobs__title",
        "profile__raw_skills",
        "educations__field__name",
        "educations__degree",
        "workexperiences__job_title",
        "workexperiences__grade",
        "workexperiences__industry__title",
        "workexperiences__skills",
        "certificateandlicenses__title",
        "certificateandlicenses__certificate_text",
    ]

    json_fields = ["resume__resume_json"]

    field_weight = "A"
    regular_vector = reduce(
        operator.add,
        [SearchVector(field, weight=field_weight) for field in fields],
    )

    json_weight = "A"
    json_vector = reduce(
        operator.add,
        [SearchVector(field, weight=json_weight) for field in json_fields],
    )

    combined_vector = regular_vector + json_vector

    queryset = User.objects.select_related("profile", "resume").prefetch_related(
        "profile__interested_jobs",
        "educations",
        "educations__field",
        "workexperiences",
        "workexperiences__industry",
        "certificateandlicenses",
    )

    keyword_groups = search_terms.keywords
    clue_words = search_terms.clue_words

    if not keyword_groups and not clue_words:
        return queryset.none()

    queryset = queryset.annotate(search=combined_vector)

    if keyword_groups:
        combined_filter = Q()

        for group_idx, keyword_group in enumerate(keyword_groups):
            if not keyword_group:
                continue

            group_filter = Q()

            for keyword in keyword_group:
                if not keyword.strip():
                    continue

                search_query = SearchQuery(keyword)
                group_filter |= Q(search=search_query)

            if group_filter != Q():
                combined_filter &= group_filter

                for keyword in keyword_group:
                    if not keyword.strip():
                        continue

                    search_query = SearchQuery(keyword)
                    rank_expression = ExpressionWrapper(
                        SearchRank(combined_vector, search_query), output_field=FloatField()
                    )
                    rank_name = f"rank_kw_{group_idx}_{keyword.replace(' ', '_')}"
                    queryset = queryset.annotate(**{rank_name: rank_expression})

        if combined_filter != Q():
            queryset = queryset.filter(combined_filter)
        else:
            return queryset.none()

    clue_word_weight = 0.5
    rank_fields = []

    all_terms = set([*clue_words, *chain.from_iterable(search_terms.keywords)])

    for clue_word in all_terms:
        if not clue_word.strip():
            continue

        search_query = SearchQuery(clue_word)
        rank_expression = ExpressionWrapper(
            SearchRank(combined_vector, search_query) * clue_word_weight, output_field=FloatField()
        )
        rank_name = f"rank_cw_{clue_word.replace(' ', '_')}"
        queryset = queryset.annotate(**{rank_name: rank_expression})
        rank_fields.append(rank_name)

    if rank_fields:
        total_expression = Value(0.0, output_field=FloatField())

        for field in rank_fields:
            total_expression = ExpressionWrapper(
                total_expression + Coalesce(F(field), Value(0.0)), output_field=FloatField()
            )

        queryset = queryset.annotate(total_rank=Sigmoid(total_expression, steepness=steepness, midpoint=midpoint))

        if not keyword_groups:
            queryset = queryset.filter(total_rank__gt=top_r)
    else:
        queryset = queryset.annotate(total_rank=Value(1.0, output_field=FloatField()))

    max_rank_subquery = queryset.values("id").annotate(max_rank=Max("total_rank")).values("id", "max_rank")

    result_queryset = (
        User.objects.filter(id__in=Subquery(max_rank_subquery.values("id")))
        .select_related("profile", "resume")
        .prefetch_related(
            "profile__interested_jobs",
            "educations",
            "educations__field",
            "workexperiences",
            "workexperiences__industry",
            "certificateandlicenses",
        )
    )

    user_rank_mapping = {item["id"]: item["max_rank"] for item in max_rank_subquery}

    case_whens = [When(id=pk, then=Value(rank)) for pk, rank in user_rank_mapping.items()]

    if case_whens:
        result_queryset = result_queryset.annotate(
            total_rank=Case(*case_whens, default=Value(0.0), output_field=FloatField())
        ).order_by("-total_rank")
    else:
        return queryset.none()

    return result_queryset
