import sys

sys.path.append("api")
from api.database import Database
from api.message_parser import get_message_node

fn = "database.json"
with open(fn, encoding="utf8") as database_file:
    db_json = database_file.read()
database = Database.model_validate_json(db_json)

num_successes = 0
for message in database.message_table.get_rows():
    html = message.content
    if "inline_image" in html:
        continue

    try:
        node = get_message_node(html)
    except AssertionError as e:
        print(f"\nERROR:\n{e}\n")
        break
    num_successes += 1
print()
print(f"{num_successes=}")
