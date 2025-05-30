from dataclasses import dataclass
from typing import Awaitable, Callable

from user import User

"""
When we render a bunch of rows that have user data in them, it can
be a bit complicated to deal with the fact that some users may not
yet have been downloaded to the client.

For example, you might be rendering a bunch of Zulip messages, but
when you start the process, your message objects may only have
sender_id, instead of the hydrated User object for sender.  Now,
usually, most of our User data is gonna be local, so it's mostly
a matter of calling something like `get_local_user` to hydrate the
user in this case (i.e. message.sender_id -> message.sender).

But because we can't rely on everything being local, we want a
more disciplined approach that handles the async stuff correctly.

Moreover, we want to ensure we don't make O(N) calls to the server,
and we certainly want to avoid even a single call to the server
if our local cache of users is sufficient for the request.

The solution here is to use a DeferredUser object in our messages.

Here is example code to populate the messages...

First, we change our message object class to use
`deferred_sender: DeferredUser` instead of `sender: User`:

    @dataclass
    class HydratedMessage:
        deferred_sender: DeferredUser # <======== NOTICE THIS!
        content: str
        timestamp: int
    
        @staticmethod
        def create(*, message: Message, factory: DeferredUserFactory) -> "HydratedMessage":
            return HydratedMessage(
                deferred_sender=factory.create_user(message.sender_id), # <==== Synchronous!
                content=message.content,
                timestamp=message.timestamp,
            )
        
Then we change our controller code to look like below.  Note that we create
our messages synchronously, and its only the call to `factory.finalize` that
has an `await` before it.

        hydrated_messages = [
            HydratedMessage.create(message=m, factory=factory) for m in messages
        ]
        helper = DeferredUserHelper(
            maybe_get_local_user=self.maybe_get_local_user,
            get_remote_users=self.get_remote_users,
        )
        await factory.finalize(helper=helper)
        return sorted(hydrated_messages, key=lambda m: m.timestamp)
        
And when we actually go to render the messages (after the `await`), we
simply do this in our render code:

    sender = hydrated_message.deferred_sender.full_object(
    # and then use sender.full_name, sender.avatar_url, etc.
"""


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
