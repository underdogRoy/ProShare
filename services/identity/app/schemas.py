from pydantic import BaseModel, EmailStr


class RegisterIn(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ProfileIn(BaseModel):
    bio: str = ""
    expertise_tags: str = ""
    links: str = ""


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str


class TokenOut(BaseModel):
    access_token: str


class ForgotPasswordOut(BaseModel):
    ok: bool = True
    message: str
    reset_url: str | None = None
