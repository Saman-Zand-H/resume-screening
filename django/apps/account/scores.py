import datetime
import math
from typing import ClassVar

from criteria.models import JobAssessment, JobAssessmentResult
from pydantic import BaseModel
from score.types import ExistingScore, Score, ScorePack
from score.utils import register_pack, register_score

from django.db.models import Count, DurationField, ExpressionWrapper, F, Sum

from .models import Profile, User


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
        name="Work Experience Verification", slug="WORK_EXPERIENCE_VERIFICATION", value=5
    )
    LANGUAGE_ADD = ScoreValue(name="Language Add", slug="LANGUAGE_ADD", value=10)
    CERTIFICATION_ADD = ScoreValue(name="Certification Add", slug="CERTIFICATION_ADD", value=10)
    SKILL_ADD = ScoreValue(name="Skill Add", slug="SKILL_ADD", value=5)
    VISA_STATUS = ScoreValue(name="Visa Status", slug="VISA_STATUS", value=10)
    JOB_INTEREST = ScoreValue(name="Job Interest", slug="JOB_INTEREST", value=10)
    COURSE_GENERAL = ScoreValue(name="Course General", slug="COURSE_GENERAL", value=20)
    ASSESSMENT_ADD = ScoreValue(name="Assessment Add", slug="ASSESSMENT_ADD", value=15)
    ASSESSMENT = ScoreValue(name="Assessment", slug="ASSESSMENT", value=200)


JOB_ASSESSMENT_SCORES_PERCENTAGE = {
    JobAssessmentResult.UserScore.AVARAGE.value: 0.25,
    JobAssessmentResult.UserScore.GOOD.value: 0.5,
    JobAssessmentResult.UserScore.GREAT.value: 0.75,
    JobAssessmentResult.UserScore.EXCEPTIONAL.value: 1,
}


def get_profile_interested_jobs(user: User):
    profile = user.get_profile()
    if not profile or not profile.interested_jobs.exists():
        return []
    return profile.interested_jobs.all()


class UserFieldExistingScore(ExistingScore):
    user_field: ClassVar[str]
    score = Scores.ID_INFORMATION.value

    def get_value(self, user):
        return getattr(user, self.user_field)


class ProfileFieldScore(UserFieldExistingScore):
    profile_field: ClassVar[str]

    def get_value(self, user):
        profile = user.get_profile()

        if profile:
            return getattr(profile, self.profile_field)


@register_score
class UploadResumeScore(Score):
    slug = "upload_resume"

    def calculate(self, user) -> int:
        from .models import Resume

        return Scores.UPLOAD_RESUME.value if Resume.objects.filter(user=user).exists() else 0


@register_score
class FirstNameScore(UserFieldExistingScore):
    slug = "first_name"
    user_field = User.first_name.field.name


@register_score
class LastNameScore(UserFieldExistingScore):
    slug = "last_name"
    user_field = User.last_name.field.name


@register_score
class GenderScore(UserFieldExistingScore):
    slug = "gender"
    user_field = User.gender.field.name


@register_score
class DateOfBirthScore(UserFieldExistingScore):
    slug = "date_of_birth"
    user_field = User.birth_date.field.name


@register_score
class EmailScore(UserFieldExistingScore):
    slug = "email"
    score = Scores.CONTACT_INFORMATION.value
    user_field = User.email.field.name


@register_score
class MobileScore(Score):
    slug = "mobile"

    def calculate(self, user) -> int:
        from .models import Contact

        return (
            Scores.CONTACT_INFORMATION.value
            if Contact.objects.filter(user=user, type=Contact.Type.PHONE).exists()
            else 0
        )


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
    slug = "education_new"

    def calculate(self, user) -> int:
        from .models import Education

        return Scores.EDUCATION_ADD.value if Education.objects.filter(user=user).exists() else 0


@register_score
class EducationVerificationScore(Score):
    slug = "education_verification"

    def calculate(self, user) -> int:
        from .models import Education

        return (
            Scores.EDUCATION_VERIFICATION.value
            if Education.objects.filter(user=user, status=Education.get_verified_statuses()).exists()
            else 0
        )


@register_score
class WorkExperienceNewScore(Score):
    slug = "work_experience_new"

    def calculate(self, user) -> int:
        from .models import WorkExperience

        years = (
            WorkExperience.objects.filter(user=user, status__in=WorkExperience.get_verified_statuses())
            .annotate(
                duration_years=ExpressionWrapper(
                    (F(WorkExperience.end.field.name) - F(WorkExperience.start.field.name)),
                    output_field=DurationField(),
                )
            )
            .aggregate(days=Sum("duration_years"))["days"]
            or datetime.timedelta()
        ).days / 365.25

        return int(math.ceil(years * 2) / 2) * Scores.WORK_EXPERIENCE_ADD.value


@register_score
class WorkExperienceVerificationScore(Score):
    slug = "work_experience_verification"

    def calculate(self, user) -> int:
        from .models import WorkExperience

        return (
            WorkExperience.objects.filter(user=user, status__in=WorkExperience.get_verified_statuses()).count()
            * Scores.WORK_EXPERIENCE_VERIFICATION.value
        )


@register_score
class LanguageScore(Score):
    slug = "language"

    def calculate(self, user) -> int:
        from .models import LanguageCertificate

        return Scores.LANGUAGE_ADD.value if LanguageCertificate.objects.filter(user=user).exists() else 0


@register_score
class CertificationScore(Score):
    slug = "certification"

    def calculate(self, user) -> int:
        from .models import CertificateAndLicense

        return Scores.CERTIFICATION_ADD.value if CertificateAndLicense.objects.filter(user=user).exists() else 0


@register_score
class SkillScore(Score):
    slug = "skill"

    def calculate(self, user) -> int:
        return Scores.SKILL_ADD.value if user.skills.exists() else 0


@register_score
class VisaStatusScore(Score):
    slug = "visa_status"

    def calculate(self, user) -> int:
        from .models import CanadaVisa

        return Scores.VISA_STATUS.value if CanadaVisa.objects.filter(user=user).exists() else 0


@register_score
class JobInterestScore(Score):
    slug = "job_interest"

    def calculate(self, user) -> int:
        if get_profile_interested_jobs(user):
            return Scores.JOB_INTEREST.value
        return 0


@register_score
class AssessmentScore(Score):
    slug = "assessment"

    def calculate(self, user) -> int:
        if not (interested_jobs := get_profile_interested_jobs(user)):
            return 0
        required = JobAssessment.objects.filter_by_required(True, interested_jobs)
        scores = (
            JobAssessmentResult.objects.filter(
                user=user,
                job_assessment__in=required,
                status=JobAssessmentResult.Status.COMPLETED,
            )
            .values(JobAssessmentResult.score.field.name)
            .annotate(count=Count(JobAssessmentResult.job_assessment.field.name, distinct=True))
        )

        if not scores:
            return 0

        total_scores = Scores.ASSESSMENT.value / sum(score["count"] for score in scores)

        return int(
            sum(
                JOB_ASSESSMENT_SCORES_PERCENTAGE.get(score[JobAssessmentResult.score.field.name], 0)
                * total_scores
                * score["count"]
                for score in scores
            )
        )


@register_score
class OptionalAssessmentScore(Score):
    slug = "optional_assessment"

    def calculate(self, user) -> int:
        if not (interested_jobs := get_profile_interested_jobs(user)):
            return 0
        optional = JobAssessment.objects.filter_by_optional(interested_jobs)

        return (
            JobAssessmentResult.objects.filter(
                user=user,
                status=JobAssessmentResult.Status.COMPLETED,
                job_assessment__in=optional,
            ).count()
            * Scores.ASSESSMENT_ADD.value
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
    ]
