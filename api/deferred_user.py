from typing import Any

from user import User

class DeferredUser:
    def __init__(self, user_id: int, *, factory: "DeferredUserFactory") -> None:
        self.user_id = user_id
        self._factory = factory

    def full_object(self) -> User:
        return self._factory.get_user(self.user_id)

class DeferredUserFactory:
    def __init__(self) -> None:
        self.user_dict: dict[int, User] = dict()
        self.user_ids: set[int] = set()
        self.finalized = False

    async def finalize(self, *, service: Any) -> None:
        remote_dict = await service.get_remote_users(self.user_ids)
        for user_id, user in remote_dict.items():
            self.user_dict[user_id] = user
        self.finalized = True

    def get_user(self, user_id: int) -> User:
        assert self.finalized
        return self.user_dict[user_id]

    def create_user(self, user_id: int) -> DeferredUser:
        self.user_ids.add(user_id)
        return DeferredUser(user_id, factory=self)
