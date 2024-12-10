from common.mixins import UserContextMixin


class CourseUserContextMixin(UserContextMixin):
    obj_context_key = "course_user"
