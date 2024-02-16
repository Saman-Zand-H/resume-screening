from django.contrib import admin

from .models import (
    Field,
    Industry,
    Job,
    JobCategory,
    LanguageProficiencyTest,
    Position,
    Skill,
    SkillTopic,
    University,
)


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = (Industry.title.field.name,)
    search_fields = (Industry.title.field.name,)


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = (JobCategory.title.field.name, JobCategory.industry.field.name)
    search_fields = (JobCategory.title.field.name,)
    list_filter = (JobCategory.industry.field.name,)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (Job.title.field.name, Job.category.field.name)
    search_fields = (Job.title.field.name,)
    list_filter = (Job.category.field.name,)


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
