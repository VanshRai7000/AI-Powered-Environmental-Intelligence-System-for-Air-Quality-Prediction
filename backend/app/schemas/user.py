from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=1, le=120)


class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    age: int        