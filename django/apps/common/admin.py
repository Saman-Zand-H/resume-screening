from django.contrib import admin

from .models import (
    Field,
    Industry,
    Job,
    JobCategory,
    LanguageProficiencySkill,
    LanguageProficiencyTest,
    Skill,
    SkillTopic,
    University,
)
from .utils import get_file_models


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
    list_display = (Field.name.field.name,)
    search_fields = (Field.name.field.name,)


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = (University.name.field.name, University.websites.field.name)
    search_fields = (University.name.field.name, University.websites.field.name)


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
    list_display = (LanguageProficiencyTest.title.field.name, LanguageProficiencyTest.languages.field.name)
    search_fields = (LanguageProficiencyTest.title.field.name,)


@admin.register(LanguageProficiencySkill)
class LanguageProficiencySkillAdmin(admin.ModelAdmin):
    list_display = (
        LanguageProficiencySkill.skill_name.field.name,
        LanguageProficiencySkill.test.field.name,
        LanguageProficiencySkill.slug.field.name,
        LanguageProficiencySkill.validators.field.name,
    )
    search_fields = list_display


for model in get_file_models():
    admin.site.register(model)
