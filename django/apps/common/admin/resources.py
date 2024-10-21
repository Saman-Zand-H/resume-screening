from import_export import fields
from import_export.resources import ModelResource

from django.utils.translation import gettext_lazy as _

from ..models import (
    Industry,
    Job,
    Field,
    University,
    LanguageProficiencySkill,
    LanguageProficiencyTest,
    JobBenefit,
    Skill,
    SkillTopic,
)


class IndustryResource(ModelResource):
    class Meta:
        model = Industry
        fields = [
            Industry.title.field.name,
        ]


class JobResource(ModelResource):
    def dehydrate_industries(self, obj: Job):
        return ", ".join(industry.title for industry in obj.industries.all())

    class Meta:
        model = Job
        fields = [
            Job.title.field.name,
            Job.industries.field.name,
        ]


class FieldResource(ModelResource):
    class Meta:
        model = Field
        fields = [
            Field.name.field.name,
        ]


class UniversityResource(ModelResource):
    def dehydrate_websites(self, obj: University):
        return ", ".join(obj.websites)

    class Meta:
        model = University
        fields = [
            University.name.field.name,
            University.websites.field.name,
        ]


class SkillTopicResource(ModelResource):
    def dehydrate_industry(self, obj: SkillTopic):
        return obj.industry.title

    class Meta:
        model = SkillTopic
        fields = [
            SkillTopic.title.field.name,
            SkillTopic.industry.field.name,
        ]


class SkillResource(ModelResource):
    def dehydrate_topic(self, obj: Skill):
        return obj.topic.title if obj.topic else ""

    class Meta:
        model = Skill
        fields = [
            Skill.title.field.name,
            Skill.insert_type.field.name,
            Skill.topic.field.name,
        ]


class LanguageProficiencyTestResource(ModelResource):
    def dehydrate_languages(self, obj: LanguageProficiencyTest):
        return ", ".join(language for language in obj.languages)

    class Meta:
        model = LanguageProficiencyTest
        fields = [
            LanguageProficiencyTest.title.field.name,
            LanguageProficiencyTest.languages.field.name,
        ]


class LanguageProficiencySkillResource(ModelResource):
    test = fields.Field(column_name=_("Test"))
    languages = fields.Field(column_name=_("Languages"))

    def dehydrate_test(self, obj: LanguageProficiencySkill):
        return obj.test.title

    def dehydrate_languages(self, obj: LanguageProficiencySkill):
        return ", ".join(language for language in obj.test.languages)

    def dehydrate_validators(self, obj: LanguageProficiencySkill):
        return ", ".join(validator for validator in obj.validators)

    class Meta:
        model = LanguageProficiencySkill
        fields = [
            LanguageProficiencySkill.skill_name.field.name,
            "test",
            "languages",
            LanguageProficiencySkill.validators.field.name,
        ]


class JobBenefitResource(ModelResource):
    class Meta:
        model = JobBenefit
        fields = [
            JobBenefit.name.field.name,
        ]
