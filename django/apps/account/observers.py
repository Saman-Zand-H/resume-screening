import contextlib
from typing import Dict

from academy.models import CourseResult
from criteria.models import JobAssessmentResult
from flex_observer.types import register_observer
from score.types import ScoreObserver

from django.db.models import Model

from .models import (
    CanadaVisa,
    CertificateAndLicense,
    Contact,
    Education,
    LanguageCertificate,
    Profile,
    Resume,
    User,
    WorkExperience,
)
from .scores import (
    AssessmentScore,
    CertificationScore,
    CityScore,
    CourseGeneralScore,
    DateOfBirthScore,
    EarlyUsersScore,
    EducationNewScore,
    EducationVerificationScore,
    EmailScore,
    FirstNameScore,
    FluentLanguageScore,
    GenderScore,
    JobInterestScore,
    LanguageScore,
    LastNameScore,
    MobileScore,
    NativeLanguageScore,
    OptionalAssessmentScore,
    SkillScore,
    UploadResumeScore,
    VisaStatusScore,
    WorkExperienceNewScore,
    WorkExperienceVerificationScore,
)


class BaseObserver[T: Model]:
    @classmethod
    def get_calculate_params(cls, instance: T) -> Dict[str, User]:
        return {"user": instance.user}

    @classmethod
    def scores_calculated(cls, instance: T, scores_dict: Dict[str, int]):
        user: User = cls.get_calculate_params(instance).get("user")
        if not (profile := getattr(user, "profile", None)):
            return
        profile.scores.update(scores_dict)
        profile.score = sum(profile.scores.values())

        with contextlib.suppress(ValueError):
            profile.save(update_fields=["score", "scores"])


@register_observer
class ProfileObserver(BaseObserver, ScoreObserver):
    _observed_model = Profile
    scores = [
        CityScore,
        FluentLanguageScore,
        NativeLanguageScore,
        GenderScore,
        JobInterestScore,
        DateOfBirthScore,
        SkillScore,
    ]


@register_observer
class UserObserver(BaseObserver, ScoreObserver):
    _observed_model = User
    scores = [
        EmailScore,
        FirstNameScore,
        LastNameScore,
        EarlyUsersScore,
    ]

    @classmethod
    def get_calculate_params(cls, instance: User):
        return {"user": instance}


@register_observer
class MobileScoreObserver(BaseObserver, ScoreObserver):
    _observed_model = Contact
    scores = [MobileScore]

    @classmethod
    def get_calculate_params(cls, instance):
        return {"user": instance.contactable.profile.user}


@register_observer
class ResumeObserver(BaseObserver, ScoreObserver):
    _observed_model = Resume
    scores = [UploadResumeScore]


@register_observer
class EducationObserver(BaseObserver, ScoreObserver):
    _observed_model = Education
    scores = [
        EducationNewScore,
        EducationVerificationScore,
    ]


@register_observer
class WorkExperienceObserver(BaseObserver, ScoreObserver):
    _observed_model = WorkExperience
    scores = [
        WorkExperienceNewScore,
        WorkExperienceVerificationScore,
    ]


@register_observer
class LanguageCertificateObserver(BaseObserver, ScoreObserver):
    _observed_model = LanguageCertificate
    scores = [LanguageScore]


@register_observer
class CertificateAndLicenseObserver(BaseObserver, ScoreObserver):
    _observed_model = CertificateAndLicense
    scores = [CertificationScore]


@register_observer
class CanadaVisaObserver(BaseObserver, ScoreObserver):
    _observed_model = CanadaVisa
    scores = [VisaStatusScore]


@register_observer
class JobAssesmentResultObserver(BaseObserver, ScoreObserver):
    _observed_model = JobAssessmentResult
    scores = [AssessmentScore, OptionalAssessmentScore]


@register_observer
class CourseObserver(BaseObserver, ScoreObserver):
    _observed_model = CourseResult
    scores = [CourseGeneralScore]
