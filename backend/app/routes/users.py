from fastapi import APIRouter, HTTPException

from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import create_user, get_user


router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=201
)
def register_user(user: UserCreate):

    created_user = create_user(user)

    return created_user


@router.get(
    "/{user_id}",
    response_model=UserResponse
)

def retrieve_user(user_id: str):

    user = get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user