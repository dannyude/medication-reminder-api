from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from pydantic import model_validator


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile_number: str

    """Validators for user with common fields and validations."""

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensures names are not empty and capitalized."""
        v = v.strip()
        if not v:
            raise ValueError("Name fields cannot be empty")
        return v.title()

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, v: str) -> str:
        """Ensures mobile number is digits only and 10-15 characters long."""
        v = v.strip()
        if not v.isdigit() or not (10 <= len(v) <= 15):
            raise ValueError("Mobile number must be 10-15 digits long")
        return v


class UserCreate(UserBase):
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self):
        """Ensures 'password' and 'confirm_password' match."""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserResponse(BaseModel):
    id: UUID  # The ID is here, in the response model
    first_name: str

    class Config:
        from_attributes = True


# 4. UserInDB (The INTERNAL model for your database)
# This is what you'd use to create the DB object.
# It has the ID and the *hashed* password.
class UserInDB(UserBase):
    id: UUID
    hashed_password: str


# A Token schema for returning JWT tokens
class Token(BaseModel):
    access_token: str
    token_type: str
    expire: int


class TokenData(BaseModel):
    user_id: UUID | None = None
