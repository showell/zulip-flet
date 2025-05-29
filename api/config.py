from configparser import ConfigParser

config = ConfigParser()
with open("zuliprc") as f:
    config.read_file(f)

HOST: str = config.get("api", "site")
USER_NAME: str = config.get("api", "email")
API_KEY: str = config.get("api", "key")