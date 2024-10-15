from flex_report.defaults.admin import TemplateAdmin as BaseTemplateAdmin
from flex_report.defaults.views import TemplateDeleteView

from django.contrib import admin
from django.urls import path

from .models import (
    Field,
    Industry,
    Job,
    JobBenefit,
    LanguageProficiencySkill,
    LanguageProficiencyTest,
    Skill,
    SkillTopic,
    University,
)
from .utils import get_file_models
from .views import (
    TemplateCreateCompleteView,
    TemplateCreateInitView,
    TemplateReportView,
    TemplateSavedFilterCreateView,
    TemplateSavedFilterUpdateView,
    TemplateUpdateView,
)


class TemplateAdmin(BaseTemplateAdmin):
    def get_urls(self):
        return [
            path(
                "add/wizard",
                self.admin_site.admin_view(TemplateCreateInitView.as_view(admin_site=self.admin_site)),
                name="flex_report_template_wizard",
            ),
            path(
                "<int:pk>/complete",
                self.admin_site.admin_view(TemplateCreateCompleteView.as_view(admin_site=self.admin_site)),
                name="flex_report_template_wizard_complete",
            ),
            path(
                "<int:pk>/edit",
                self.admin_site.admin_view(TemplateUpdateView.as_view(admin_site=self.admin_site)),
                name="flex_report_template_edit",
            ),
            path(
                "<int:pk>/filter",
                self.admin_site.admin_view(TemplateSavedFilterCreateView.as_view(admin_site=self.admin_site)),
                name="flex_report_template_filter",
            ),
            path(
                "<int:pk>/filter/<int:filter_pk>",
                self.admin_site.admin_view(TemplateSavedFilterUpdateView.as_view(admin_site=self.admin_site)),
                name="flex_report_template_filter_update",
            ),
            path(
                "<int:pk>/report",
                self.admin_site.admin_view(TemplateReportView.as_view(admin_site=self.admin_site)),
                name="flex_report_template_report",
            ),
            path(
                "<int:pk>/delete",
                self.admin_site.admin_view(TemplateDeleteView.as_view()),
                name="flex_report_template_delete",
            ),
            *super().get_urls(),
        ]


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = (Industry.title.field.name,)
    search_fields = (Industry.title.field.name,)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (Job.title.field.name, Job.order.field.name)
    search_fields = (Job.title.field.name,)
    list_filter = (Job.industries.field.name,)
    autocomplete_fields = (Job.industries.field.name,)


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
    autocomplete_fields = (SkillTopic.industry.field.name,)


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
    autocomplete_fields = (LanguageProficiencySkill.test.field.name,)


@admin.register(JobBenefit)
class JobBenefitsAdmin(admin.ModelAdmin):
    list_display = (
        JobBenefit.id.field.name,
        JobBenefit.name.field.name,
    )
    search_fields = (JobBenefit.name.field.name,)


for model in get_file_models():
    admin.site.register(model)
