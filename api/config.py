from configparser import ConfigParser

config = ConfigParser()

try:
    with open("zuliprc") as f:
        config.read_file(f)
except FileNotFoundError:
    print("""
        ERROR: You need a zuliprc file to fetch Zulip data.
        
        Follow https://zulip.com/api/api-keys#get-your-api-key to see how to
        get your API key, but the last step should be to click
        on the "Download zuliprc" button.  Copy the zuliprc to your
        working directory (i.e. here, most likely).
    """)
    raise

HOST: str = config.get("api", "site")
USER_NAME: str = config.get("api", "email")
API_KEY: str = config.get("api", "key")
