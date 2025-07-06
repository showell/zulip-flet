import sys
import time

sys.path.append("api")
from api.database import Database
from api.message_node import BaseNode
from api.message_parser import get_message_node

fn = "database.json"
with open(fn, encoding="utf8") as database_file:
    db_json = database_file.read()
database = Database.model_validate_json(db_json)

num_successes = 0
nodes: list[BaseNode] = []
for message in database.message_table.get_rows():
    html = message.content

    try:
        node = get_message_node(html)
        node.as_text()
        node.as_html()
    except AssertionError as e:
        print(f"\nOUTER HMTL:\n{repr(html)}")
        print(f"\nERROR:\n{e}\n")
        break

    nodes.append(node)
    num_successes += 1
print()
print(f"{num_successes=}")

t = time.time()
reps = 200
assert reps * len(nodes) == 1_000_000
for _ in range(reps):
    for node in nodes:
        node.as_html()

# On my dusty old Dell laptop, the average cost
# of calling as_html() on a fairly representative
# sample of Zulip messages is about 60 microseconds.
print("elapsed", time.time() - t)
