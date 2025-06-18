from typing import Any

from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    avatar_url: str

    @staticmethod
    def from_raw(host: str, realm_user: dict[str, Any]) -> "User":
        avatar_url = realm_user["avatar_url"]
        if avatar_url.startswith("/"):
            avatar_url = host + avatar_url
        return User(
            id=realm_user["user_id"],
            name=realm_user["full_name"],
            avatar_url=avatar_url,
        )
