"""
models/user.py
──────────────
Pydantic v2 models for the User domain.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field, field_validator, model_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    email: str
    age: int
    role: str = "viewer"

    @field_validator("email")
    @classmethod
    def email_must_have_at(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower()

    @field_validator("age")
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Age must be positive")
        return v

    @model_validator(mode="after")
    def admin_must_be_adult(self) -> "UserCreate":
        if self.role == "admin" and self.age < 18:
            raise ValueError("Admin users must be 18+")
        return self


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    age: int
    role: str
    created_at: datetime

    @computed_field
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
