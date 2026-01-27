import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo

from api.src.users.models import UserStatus


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    mobile_number: str | None = None
    status: UserStatus
    created_at: datetime
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class ChangePasswordSchema(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)
    confirm_new_password: str = Field(..., min_length=6)

# Forgot password schema
class ForgotPasswordSchema(BaseModel):
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
            }
        }

# Reset password schema
class ResetPasswordSchema(BaseModel):
    reset_token: str = Field(
        description="Password reset token sent via email",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    new_password: str = Field(
        min_length=8,
        description="New account password (minimum 8 characters)",
        examples=["StrongP@ssw0rd"]
    )
    confirm_new_password: str = Field(
        min_length=8,
        description="Must match the new password",
        examples=["StrongP@ssw0rd"]
    )

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        # (This part is perfectly fine!)
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @field_validator('confirm_new_password')
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo):
        """Ensure new_password and confirm_new_password match."""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('New password and confirmation do not match')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "StrongP@ssw0rd",
                "confirm_new_password": "StrongP@ssw0rd"
            }
        }
    }