import logging

from ._client import BaseAcademyClient
from .types import (
    EnrollUserInCourseRequest,
    EnrollUserInCourseResponse,
    GenerateLoginUrlRequest,
    GenerateLoginUrlResponse,
    GetCourseUrlByIdRequest,
    GetCourseUrlByIdResponse,
    GetOrCreateUserRequest,
    GetOrCreateUserResponse,
    GetUserByExternalIdRequest,
    GetUserByExternalIdResponse,
)

logger = logging.getLogger(__name__)


class AcademyClient(BaseAcademyClient):
    def get_or_create_user(self, user_data: GetOrCreateUserRequest) -> GetOrCreateUserResponse:
        return self._make_request(
            "POST",
            "getOrCreateUser",
            model=GetOrCreateUserResponse,
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

    def get_user_by_external_id(self, external_id_data: GetUserByExternalIdRequest) -> GetUserByExternalIdResponse:
        return self._make_request(
            "GET",
            f"user?external_id={external_id_data.external_id}",
            model=GetUserByExternalIdResponse,
        )

    def get_coures_url_by_id(self, course_id_data: GetCourseUrlByIdRequest) -> GetCourseUrlByIdResponse:
        return self._make_request(
            "GET",
            f"getCourseUrl?course_id={course_id_data.course_id}",
            model=GetCourseUrlByIdResponse,
        )


academy_client = AcademyClient()
