from common.mixins import UserContextMixin


class JobAssessmentUserContextMixin(UserContextMixin):
    obj_context_key = "job_assessment_user"
