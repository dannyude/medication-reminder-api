import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from api.src.users.models import UserStatus


class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    email: EmailStr = Field(..., description="Email address")
    mobile_number: str = Field(..., min_length=10, max_length=15, description="Mobile number")

    # Validators for the fields
    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensures names are not empty and capitalized."""
        v = v.strip()
        if not v:
            raise ValueError("Name fields cannot be empty")

        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.title()

    # validator for mobile number
    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        """Validate and sanitize mobile number."""
        v = v.strip()

        # Regex: Remove spaces, hyphens, parentheses
        # We keep '+' because we want to know if it's international
        cleaned = re.sub(r'[\s\-\(\)]', '', v)

        # Check for + prefix for the isdigit check
        digits_only = cleaned[1:] if cleaned.startswith('+') else cleaned

        # Check if actual digits
        if not digits_only.isdigit():
            raise ValueError('Mobile number must contain only digits (and optional +)')

        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError('Mobile number must be between 10 and 15 digits')

        return cleaned



class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password")
    confirm_password: str = Field(..., min_length=8, description="Confirm Password")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:

        v = v.strip()

        # 2. Check Length
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        # 3. Check Complexity
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')

        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')

        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')

        return v

    @model_validator(mode="after")
    def check_passwords_match(self):
        """Ensures 'password' and 'confirm_password' match."""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


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

class ResponseMessage(BaseModel):
    user: UserResponseSchema
    message: str
