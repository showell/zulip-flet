from dataclasses import dataclass
from typing import Awaitable, Callable

from user import User


@dataclass
class DeferredUserHelper:
    maybe_get_local_user: Callable[[int], User | None]
    get_remote_users: Callable[[set[int]], Awaitable[dict[int, User]]]


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

    def create_user(self, user_id: int) -> DeferredUser:
        self.user_ids.add(user_id)
        return DeferredUser(user_id, factory=self)

    async def finalize(self, *, helper: DeferredUserHelper) -> None:
        remote_user_ids: set[int] = set()

        for user_id in self.user_ids:
            maybe_user = helper.maybe_get_local_user(user_id)
            if maybe_user is None:
                remote_user_ids.add(user_id)
            else:
                self.user_dict[user_id] = maybe_user

        if remote_user_ids:
            remote_dict = await helper.get_remote_users(remote_user_ids)
            for user_id, user in remote_dict.items():
                self.user_dict[user_id] = user
        self.finalized = True

    def get_user(self, user_id: int) -> User:
        assert self.finalized
        return self.user_dict[user_id]
