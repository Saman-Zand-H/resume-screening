import logging

from ._client import BaseAcademyClient
from .types import (
    CreateOrUpdateUserRequest,
    CreateOrUpdateUserResponse,
    EnrollUserInCourseRequest,
    EnrollUserInCourseResponse,
    GenerateLoginUrlRequest,
    GenerateLoginUrlResponse,
    GetCourseUrlByIdRequest,
    GetCourseUrlByIdResponse,
    GetUsersByExternalIdRequest,
    GetUsersByExternalIdResponse,
)

logger = logging.getLogger(__name__)


class AcademyClient(BaseAcademyClient):
    def create_or_update_user(self, user_data: CreateOrUpdateUserRequest) -> CreateOrUpdateUserResponse:
        return self._make_request(
            "POST",
            "createOrUpdateUser",
            model=CreateOrUpdateUserResponse,
            json=user_data.model_dump(exclude_unset=True),
        )

    def enroll_user_in_course(self, enrollment_data: EnrollUserInCourseRequest) -> EnrollUserInCourseResponse:
        return self._make_request(
            "POST",
            "enrollUserInCourse",
            model=EnrollUserInCourseResponse,
            json=enrollment_data.model_dump(exclude_unset=True),
        )

    def generate_login_url(self, login_data: GenerateLoginUrlRequest) -> GenerateLoginUrlResponse:
        return self._make_request(
            "POST",
            "generateLoginUrl",
            model=GenerateLoginUrlResponse,
            json=login_data.model_dump(exclude_unset=True),
        )

    def get_users_by_external_id(self, external_id_data: GetUsersByExternalIdRequest) -> GetUsersByExternalIdResponse:
        return self._make_request(
            "GET",
            f"users?user_external_id={external_id_data.user_external_id}",
            model=GetUsersByExternalIdResponse,
        )

    def get_coures_url_by_id(self, course_id_data: GetCourseUrlByIdRequest) -> GetCourseUrlByIdResponse:
        return self._make_request(
            "GET",
            f"getCourseUrl?course_id={course_id_data.course_id}",
            model=GetCourseUrlByIdResponse,
        )


academy_client = AcademyClient()
