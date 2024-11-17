from common.mixins import UserContextMixin

from .constants import COURSE_USER_CONTEXT_KEY


class CourseUserContextMixin(UserContextMixin):
    user_context_key = COURSE_USER_CONTEXT_KEY
