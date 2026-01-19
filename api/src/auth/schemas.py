import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from api.src.users.models import UserStatus


# class Token(BaseModel):
#     access_token: str
#     token_type: str
#     expire: int


# class TokenData(BaseModel):
#     user_id: UUID | None = None


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    mobile_number: str | None = None  # Use | None if it can be empty
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
    delivery_method: str = Field(default="sms", pattern="^(sms|email)$")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "delivery_method": "sms"
            }
        }
# Reset password schema
class ResetPasswordSchema(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
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

    class Config:
        json_schema_extra = {
            "example": {
                "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "NewPassword123!"
            }
        }


class VerifyOTPSchema(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern="^\d{6}$")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp": "123456"
            }
        }

