import contextlib
import datetime
import math
from typing import ClassVar

from academy.models import CourseResult
from common.utils import fields_join
from criteria.models import JobAssessment, JobAssessmentResult
from pydantic import BaseModel
from score.types import ExistingScore, Score, ScorePack
from score.utils import register_pack, register_score

from django.db.models import Case, Count, DurationField, ExpressionWrapper, F, Sum, When
from django.db.models.functions import Now
from django.db.models.lookups import In, IsNull

from .constants import EARLY_USERS_COUNT
from .models import (
    CanadaVisa,
    CertificateAndLicense,
    Contact,
    Contactable,
    Education,
    LanguageCertificate,
    Profile,
    Resume,
    User,
    WorkExperience,
)


class ScoreValue(BaseModel):
    name: str
    slug: str
    value: int


class Scores:
    UPLOAD_RESUME = ScoreValue(name="Upload Resume", slug="UPLOAD_RESUME", value=20)
    ID_INFORMATION = ScoreValue(name="ID Information", slug="ID_INFORMATION", value=5)
    CONTACT_INFORMATION = ScoreValue(name="Contact Information", slug="CONTACT_INFORMATION", value=10)
    EDUCATION_ADD = ScoreValue(name="Education Add", slug="EDUCATION_ADD", value=5)
    EDUCATION_VERIFICATION = ScoreValue(name="Education Verification", slug="EDUCATION_VERIFICATION", value=5)
    WORK_EXPERIENCE_ADD = ScoreValue(name="Work Experience Add", slug="WORK_EXPERIENCE_ADD", value=1)
    WORK_EXPERIENCE_VERIFICATION = ScoreValue(
        name="Work Experience Verification",
        slug="WORK_EXPERIENCE_VERIFICATION",
        value=5,
    )
    LANGUAGE_ADD = ScoreValue(name="Language Add", slug="LANGUAGE_ADD", value=10)
    CERTIFICATION_ADD = ScoreValue(name="Certification Add", slug="CERTIFICATION_ADD", value=10)
    SKILL_ADD = ScoreValue(name="Skill Add", slug="SKILL_ADD", value=5)
    VISA_STATUS = ScoreValue(name="Visa Status", slug="VISA_STATUS", value=10)
    JOB_INTEREST = ScoreValue(name="Job Interest", slug="JOB_INTEREST", value=10)
    COURSE_GENERAL = ScoreValue(name="Course General", slug="COURSE_GENERAL", value=20)
    ASSESSMENT_ADD = ScoreValue(name="Assessment Add", slug="ASSESSMENT_ADD", value=15)
    ASSESSMENT = ScoreValue(name="Assessment", slug="ASSESSMENT", value=200)
    EARLY_USERS = ScoreValue(name="Early Users", slug="EARLY_USERS", value=100)


JOB_ASSESSMENT_SCORES_PERCENTAGE = {
    JobAssessmentResult.UserScore.AVARAGE.value: 0.25,
    JobAssessmentResult.UserScore.GOOD.value: 0.5,
    JobAssessmentResult.UserScore.GREAT.value: 0.75,
    JobAssessmentResult.UserScore.EXCEPTIONAL.value: 1,
}


class UserFieldExistingScore(ExistingScore):
    user_field: ClassVar[str]
    score = Scores.ID_INFORMATION.value

    @classmethod
    def get_observed_fields(cls):
        return [cls.user_field]

    def get_value(self, user):
        return getattr(user, self.user_field)


class ProfileFieldScore(UserFieldExistingScore):
    profile_field: ClassVar[str]

    @classmethod
    def get_observed_fields(cls):
        return [cls.profile_field]

    def get_value(self, user):
        return getattr(user.profile, self.profile_field)


@register_score
class UploadResumeScore(Score):
    slug = "upload_resume"

    observed_fields = [Resume.id.field.name]

    def calculate(self, user) -> int:
        return Scores.UPLOAD_RESUME.value if Resume.objects.filter(**{fields_join(Resume.user): user}).exists() else 0


@register_score
class FirstNameScore(UserFieldExistingScore):
    slug = "first_name"
    user_field = User.first_name.field.name


@register_score
class LastNameScore(UserFieldExistingScore):
    slug = "last_name"
    user_field = User.last_name.field.name


@register_score
class EarlyUsersScore(Score):
    slug = "early_users"
    observed_fields = [User.id.field.name]

    @classmethod
    def test_func(cls, instance: User):
        early_users = User.objects.order_by(fields_join(User.date_joined))[:EARLY_USERS_COUNT].values_list(
            User._meta.pk.attname,
            flat=True,
        )

        return (
            User.objects.filter(**{fields_join(User._meta.pk.attname, In.lookup_name): early_users})
            .filter(**{User._meta.pk.attname: instance.id})
            .exists()
        )

    def calculate(self, user) -> int:
        return Scores.EARLY_USERS.value


@register_score
class EmailScore(UserFieldExistingScore):
    slug = "email"
    score = Scores.CONTACT_INFORMATION.value
    user_field = User.email.field.name


@register_score
class MobileScore(Score):
    slug = "mobile"
    observed_fields = [Contact.id.field.name]

    @classmethod
    def test_func(cls, instance):
        with contextlib.suppress(Contactable.DoesNotExist):
            return instance.type == Contact.Type.PHONE and hasattr(instance.contactable, "profile")

    def calculate(self, user) -> int:
        return (
            Scores.CONTACT_INFORMATION.value
            if Contact.objects.filter(
                **{
                    fields_join(
                        Contact.contactable,
                        Profile.contactable.field.related_query_name(),
                        Profile.user,
                    ): user,
                    fields_join(Contact.type): Contact.Type.PHONE,
                }
            ).exists()
            else 0
        )


@register_score
class GenderScore(ProfileFieldScore):
    slug = "gender"
    profile_field = Profile.gender.field.name


@register_score
class DateOfBirthScore(ProfileFieldScore):
    slug = "date_of_birth"
    profile_field = Profile.birth_date.field.name


@register_score
class CityScore(ProfileFieldScore):
    slug = "city"
    score = Scores.CONTACT_INFORMATION.value
    profile_field = Profile.city.field.name


@register_score
class FluentLanguageScore(ProfileFieldScore):
    slug = "fluent_language"
    score = Scores.ID_INFORMATION.value
    profile_field = Profile.fluent_languages.field.name


@register_score
class NativeLanguageScore(ProfileFieldScore):
    slug = "native_language"
    score = Scores.ID_INFORMATION.value
    profile_field = Profile.native_language.field.name


@register_score
class EducationNewScore(Score):
    observed_fields = [Education.status.field.name, Education.id.field.name]
    slug = "education_new"

    def calculate(self, user) -> int:
        return (
            Scores.EDUCATION_ADD.value
            if Education.objects.filter(**{fields_join(Education.user): user}).exists()
            else 0
        )


@register_score
class EducationVerificationScore(Score):
    slug = "education_verification"
    observed_fields = [Education.status.field.name, Education.id.field.name]

    @classmethod
    def test_func(cls, instance: Education):
        return instance.status in Education.get_verified_statuses()

    def calculate(self, user) -> int:
        return (
            Scores.EDUCATION_VERIFICATION.value
            if Education.objects.filter(
                **{fields_join(Education.user): user, fields_join(Education.status): Education.get_verified_statuses()}
            ).exists()
            else 0
        )


@register_score
class WorkExperienceNewScore(Score):
    observed_fields = [
        WorkExperience.status.field.name,
        WorkExperience.id.field.name,
        WorkExperience.end.field.name,
        WorkExperience.start.field.name,
    ]
    slug = "work_experience_new"

    def calculate(self, user) -> int:
        years = (
            WorkExperience.objects.filter(**{fields_join(WorkExperience.user): user})
            .annotate(
                duration_years=ExpressionWrapper(
                    (
                        Case(
                            When(**{fields_join(WorkExperience.end, IsNull.lookup_name): True}, then=Now()),
                            default=F(WorkExperience.end.field.name),
                        )
                        - F(WorkExperience.start.field.name)
                    ),
                    output_field=DurationField(),
                )
            )
            .aggregate(days=Sum(ExpressionWrapper(F("duration_years"), output_field=DurationField())))["days"]
            or datetime.timedelta()
        ).days / 365.25

        return int(math.ceil(years * 2) / 2) * Scores.WORK_EXPERIENCE_ADD.value


@register_score
class WorkExperienceVerificationScore(Score):
    slug = "work_experience_verification"
    observed_fields = [WorkExperience.id.field.name, WorkExperience.status.field.name]

    @classmethod
    def test_func(self, instance: WorkExperience):
        return instance.status in WorkExperience.get_verified_statuses()

    def calculate(self, user) -> int:
        return (
            WorkExperience.objects.filter(
                **{
                    fields_join(WorkExperience.user): user,
                    fields_join(WorkExperience.status, In.lookup_name): WorkExperience.get_verified_statuses(),
                }
            ).count()
            * Scores.WORK_EXPERIENCE_VERIFICATION.value
        )


@register_score
class LanguageScore(Score):
    observed_fields = [LanguageCertificate.id.field.name]
    slug = "language"

    def calculate(self, user) -> int:
        return (
            Scores.LANGUAGE_ADD.value
            if LanguageCertificate.objects.filter(**{fields_join(LanguageCertificate.user): user}).exists()
            else 0
        )


@register_score
class CertificationScore(Score):
    observed_fields = [CertificateAndLicense.id.field.name]
    slug = "certification"

    def calculate(self, user) -> int:
        return (
            Scores.CERTIFICATION_ADD.value
            if CertificateAndLicense.objects.filter(**{fields_join(CertificateAndLicense.user): user}).exists()
            else 0
        )


@register_score
class SkillScore(Score):
    observed_fields = [Profile.skills.field.name]
    slug = "skill"

    def calculate(self, user) -> int:
        return Scores.SKILL_ADD.value if user.profile.skills.exists() else 0


@register_score
class VisaStatusScore(Score):
    observed_fields = [CanadaVisa.id.field.name]
    slug = "visa_status"

    def calculate(self, user) -> int:
        return (
            Scores.VISA_STATUS.value
            if CanadaVisa.objects.filter(**{fields_join(CanadaVisa.user): user}).exists()
            else 0
        )


@register_score
class JobInterestScore(Score):
    observed_fields = [Profile.interested_jobs.field.name]
    slug = "job_interest"

    def calculate(self, user) -> int:
        return Scores.JOB_INTEREST.value if user.profile.interested_jobs.exists() else 0


@register_score
class AssessmentScore(Score):
    observed_fields = [JobAssessmentResult.id.field.name]
    slug = "assessment"

    def calculate(self, user) -> int:
        if not (interested_jobs := user.profile.interested_jobs.all()):
            return 0
        required = JobAssessment.objects.filter_by_required(True, interested_jobs)
        scores = (
            JobAssessmentResult.objects.filter(
                **{
                    fields_join(JobAssessmentResult.user): user,
                    fields_join(JobAssessmentResult.job_assessment, In.lookup_name): required,
                    fields_join(JobAssessmentResult.status): JobAssessmentResult.Status.COMPLETED,
                },
            )
            .values(fields_join(JobAssessmentResult.score))
            .annotate(count=Count(fields_join(JobAssessmentResult.job_assessment), distinct=True))
        )

        if not scores:
            return 0

        total_scores = Scores.ASSESSMENT.value / sum(score["count"] for score in scores)

        return int(
            sum(
                JOB_ASSESSMENT_SCORES_PERCENTAGE.get(score[fields_join(JobAssessmentResult.score)], 0)
                * total_scores
                * score["count"]
                for score in scores
            )
        )


@register_score
class OptionalAssessmentScore(Score):
    observed_fields = [JobAssessmentResult.id.field.name]
    slug = "optional_assessment"

    def calculate(self, user) -> int:
        if not (interested_jobs := user.profile.interested_jobs.all()):
            return 0
        optional = JobAssessment.objects.filter_by_optional(interested_jobs)

        return (
            JobAssessmentResult.objects.filter(
                **{
                    fields_join(JobAssessmentResult.user): user,
                    fields_join(JobAssessmentResult.job_assessment, In.lookup_name): optional,
                    fields_join(JobAssessmentResult.status): JobAssessmentResult.Status.COMPLETED,
                },
            ).count()
            * Scores.ASSESSMENT_ADD.value
        )


@register_score
class CourseGeneralScore(Score):
    observed_fields = [CourseResult.id.field.name, CourseResult.status.field.name]
    slug = "course_general"

    def calculate(self, user) -> int:
        return (
            CourseResult.objects.filter(
                **{
                    fields_join(CourseResult.user): user,
                    fields_join(CourseResult.status): CourseResult.Status.COMPLETED,
                }
            ).count()
            * Scores.COURSE_GENERAL.value
        )


@register_pack
class UserScorePack(ScorePack):
    slug = "user_score_pack"
    scores = [
        UploadResumeScore,
        FirstNameScore,
        LastNameScore,
        GenderScore,
        DateOfBirthScore,
        EmailScore,
        CityScore,
        MobileScore,
        EducationNewScore,
        EducationVerificationScore,
        WorkExperienceNewScore,
        WorkExperienceVerificationScore,
        LanguageScore,
        FluentLanguageScore,
        NativeLanguageScore,
        CertificationScore,
        SkillScore,
        VisaStatusScore,
        JobInterestScore,
        AssessmentScore,
        OptionalAssessmentScore,
        CourseGeneralScore,
    ]
