from pydantic import BaseModel, EmailStr


class LoginForm(BaseModel):
    email: str
    password: str
