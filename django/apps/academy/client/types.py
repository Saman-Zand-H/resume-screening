from enum import Enum

from pydantic import BaseModel


class GetOrCreateUserRequest(BaseModel):
    external_id: str
    email: str
    first_name: str
    last_name: str


class GetOrCreateUserResponse(BaseModel):
    user_id: int


class EnrollUserInCourseRequest(BaseModel):
    user_id: int
    course_id: int


class EnrollUserInCourseResponse(BaseModel):
    message: str


class GenerateLoginUrlRequest(BaseModel):
    user_id: int
    redirect_uri: str


class GenerateLoginUrlResponse(BaseModel):
    login_url: str


class GetUserByExternalIdRequest(BaseModel):
    external_id: str


class GetUserByExternalIdResponse(BaseModel):
    user_id: int


class GetCourseUrlByIdRequest(BaseModel):
    course_id: int


class GetCourseUrlByIdResponse(BaseModel):
    url: str


class CollegeCourseStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"


class CourseCompletaionResponse(BaseModel):
    course_id: str
    external_id: str
    status: CollegeCourseStatus
