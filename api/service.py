import data_layer

class Service:
    def __init__(self, database):
        self.database = database

    async def get_users(self):
        return self.database.user_dict.values()

    async def get_user(self, user_id):
        return self.database.user_dict[user_id]

    async def get_messages(self):
        return self.database.message_dict.values()

async def get_service():
    database = await data_layer.get_database()
    return Service(database)