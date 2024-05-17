from pydantic import BaseModel


class CreateOrUpdateUserRequest(BaseModel):
    user_external_id: str
    email: str
    first_name: str
    last_name: str


class CreateOrUpdateUserResponse(BaseModel):
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


class GetUsersByExternalIdRequest(BaseModel):
    user_external_id: str


class GetUsersByExternalIdResponse(BaseModel):
    id: int


class GetCourseUrlByIdRequest(BaseModel):
    course_id: int


class GetCourseUrlByIdResponse(BaseModel):
    url: str
