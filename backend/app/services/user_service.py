from uuid import uuid4

from app.schemas.user import UserCreate


users_db: dict[str, dict] = {}


def create_user(user: UserCreate):
    user_id = str(uuid4())

    user_data = {
        "user_id": user_id,
        "name": user.name,
        "email": user.email,
        "age": user.age
    }

    users_db[user_id] = user_data

    return user_data


def get_user(user_id: str):
    return users_db.get(user_id)