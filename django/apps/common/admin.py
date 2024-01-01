from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import Field, Job, JobCategory, JobIndustry, University, Skill, Position, Language, LanguageProficiencyTest


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(JobIndustry)
class JobIndustryAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "industry")
    search_fields = ("title", "category__title", "industry__title")
    list_filter = ("category", "industry")


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    list_filter = ("name",)


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "website")
    search_fields = ("name", "city__name", "website")
    list_filter = ("name",)
    raw_id_fields = ("city",)


@admin.register(Skill)
class SkillAdmin(MPTTModelAdmin):
    list_display = (
        "id",
        "title",
        "parent",
        "job",
    )
    search_fields = (
        "title",
        "parent__title",
    )


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code")
    search_fields = ("name", "code")


@admin.register(LanguageProficiencyTest)
class LanguageProficiencyTestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
    )
    search_fields = ("title",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
    )
    search_fields = ("title",)
