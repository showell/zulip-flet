from pydantic import BaseModel

from user import User


class UserTable(BaseModel):
    table: dict[int, User] = {}

    def get_row(self, id: int) -> User:
        return self.table[id]

    def maybe_get_row(self, id: int) -> User | None:
        return self.table.get(id, None)

    def get_rows(self) -> list[User]:
        return list(self.table.values())

    def insert(self, row: User) -> None:
        self.table[row.id] = row
