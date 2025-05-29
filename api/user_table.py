from pydantic import BaseModel

from user import User


class UserTable(BaseModel):
    table: dict[int, User] = {}

    def get_row(self, id):
        return self.table[id]

    def get_rows(self):
        return self.table.values()

    def insert(self, row):
        self.table[row.id] = row
