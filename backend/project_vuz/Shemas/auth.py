from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    study_group: str = Field(min_length=1, max_length=32)
    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)


class CheckStudentRequest(BaseModel):
    study_group: str = Field(min_length=1, max_length=32)
    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)


class CheckStudentResponse(BaseModel):
    found: bool
    already_registered: bool = False
    full_name: str | None = None
    study_group: str | None = None
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthTokenResponse(BaseModel):
    """Ответ после входа или регистрации."""

    access_token: str
    token_type: str = "bearer"
    student_id: int
    email: EmailStr
    full_name: str
    study_group: str
    available_points: int


class CurrentUserResponse(BaseModel):
    """Текущий пользователь по Bearer-токену (без нового JWT)."""

    student_id: int
    email: EmailStr
    full_name: str
    study_group: str
    available_points: int
