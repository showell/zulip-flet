import data_layer

class Service:
    def __init__(self, database):
        self.database = database

    async def get_users(self):
        return self.database.user_table.get_rows()

    async def get_user(self, user_id):
        return self.database.user_table.get_row(user_id)

    async def get_messages(self):
        return self.database.message_table.get_rows()

async def get_service():
    database = await data_layer.get_database()
    return Service(database)