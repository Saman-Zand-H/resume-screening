from common.mixins import UserContextMixin


class JobAssessmentUserContextMixin(UserContextMixin):
    user_context_key = "job_assessment_user"
