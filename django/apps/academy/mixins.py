from common.mixins import UserContextMixin


class CourseUserContextMixin(UserContextMixin):
    user_context_key = "course_user"
