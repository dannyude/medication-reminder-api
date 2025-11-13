from pydantic import BaseModel, EmailStr
from uuid import UUID
from pydantic import model_validator


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile_number: str


class UserCreate(UserBase):
    password: str
    confirm_password: str
    @model_validator(mode='after')
    def check_passwords_match(self):
        """Ensures 'password' and 'confirm_password' match."""
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
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