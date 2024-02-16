from django.contrib import admin

from .models import (
    Field,
    Job,
    JobCategory,
    JobIndustry,
    LanguageProficiencyTest,
    Position,
    Skill,
    SkillTopic,
    University,
)


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


@admin.register(SkillTopic)
class SkillTopicAdmin(admin.ModelAdmin):
    list_display = (SkillTopic.title.field.name, SkillTopic.industry.field.name)
    search_fields = (SkillTopic.title.field.name,)
    list_filter = (SkillTopic.industry.field.name,)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = (
        Skill.title.field.name,
        Skill.insert_type.field.name,
    )
    search_fields = (Skill.title.field.name,)
    list_filter = (Skill.insert_type.field.name,)


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
