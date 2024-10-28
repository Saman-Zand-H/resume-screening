from import_export import fields
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, JSONWidget

from django.utils.translation import gettext_lazy as _

from ..models import (
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
from ..widgets import ArrayFieldWidget


class IndustryResource(ModelResource):
    class Meta:
        model = Industry


class JobResource(ModelResource):
    industries = fields.Field(
        column_name=_("Industries"),
        attribute=Job.industries.field.name,
        widget=ManyToManyWidget(Industry, field=Industry.title.field.name, separator="-"),
    )

    class Meta:
        model = Job
        fields = [
            Job.id.field.name,
            Job.title.field.name,
            Job.industries.field.name,
            Job.require_appearance_data.field.name,
            Job.order.field.name,
        ]
        import_id_fields = [Job.id.field.name]


class FieldResource(ModelResource):
    class Meta:
        model = Field


class UniversityResource(ModelResource):
    websites = fields.Field(
        column_name=_("Websites"), attribute=University.websites.field.name, widget=ArrayFieldWidget()
    )

    class Meta:
        model = University
        fields = [
            University.id.field.name,
            University.name.field.name,
            University.websites.field.name,
        ]
        import_id_fields = [University.id.field.name]


class SkillTopicResource(ModelResource):
    industry = fields.Field(
        column_name=_("Industry"),
        attribute=SkillTopic.industry.field.name,
        widget=ForeignKeyWidget(Industry, Industry.title.field.name),
    )

    class Meta:
        model = SkillTopic
        fields = [
            SkillTopic.id.field.name,
            SkillTopic.title.field.name,
            SkillTopic.industry.field.name,
        ]
        import_id_fields = [SkillTopic.id.field.name]


class SkillResource(ModelResource):
    topic = fields.Field(
        column_name=_("Topic"),
        attribute=Skill.topic.field.name,
        widget=ForeignKeyWidget(SkillTopic, SkillTopic.title.field.name),
    )

    class Meta:
        model = Skill
        fields = [
            Skill.id.field.name,
            Skill.title.field.name,
            Skill.insert_type.field.name,
            Skill.topic.field.name,
        ]
        import_id_fields = [Skill.id.field.name]


class LanguageProficiencyTestResource(ModelResource):
    languages = fields.Field(
        column_name=_("Languages"), attribute=LanguageProficiencyTest.languages.field.name, widget=ArrayFieldWidget()
    )

    class Meta:
        model = LanguageProficiencyTest
        fields = [
            LanguageProficiencyTest.id.field.name,
            LanguageProficiencyTest.title.field.name,
            LanguageProficiencyTest.languages.field.name,
        ]
        import_id_fields = [LanguageProficiencyTest.id.field.name]


class LanguageProficiencySkillResource(ModelResource):
    test = fields.Field(
        column_name=_("Test"),
        attribute=LanguageProficiencySkill.test.field.name,
        widget=ForeignKeyWidget(LanguageProficiencyTest, "title"),
    )
    validators = fields.Field(
        column_name=_("Validators"), attribute=LanguageProficiencySkill.validators.field.name, widget=ArrayFieldWidget()
    )
    validator_kwargs = fields.Field(
        column_name=_("Validator kwargs"),
        attribute=LanguageProficiencySkill.validator_kwargs.field.name,
        widget=JSONWidget(),
    )

    class Meta:
        model = LanguageProficiencySkill
        fields = [
            LanguageProficiencySkill.id.field.name,
            LanguageProficiencySkill.slug.field.name,
            LanguageProficiencySkill.skill_name.field.name,
            LanguageProficiencySkill.test.field.name,
            LanguageProficiencySkill.validators.field.name,
            LanguageProficiencySkill.validator_kwargs.field.name,
        ]
        import_id_fields = [LanguageProficiencySkill.id.field.name]


class JobBenefitResource(ModelResource):
    class Meta:
        model = JobBenefit
