import json
import sys

sys.path.append("api")
from api.database import Database
from api.message_node import BaseNode
from api.message_parser import IllegalMessage, get_message_node


def test_valid_messages(messages):
    num_successes = 0
    nodes: list[BaseNode] = []
    for html in messages:
        try:
            node = get_message_node(html)
            node.as_text()
            node.as_html()
        except IllegalMessage as e:
            print(f"\nOUTER HMTL:\n{repr(html)}")
            print(f"\nERROR:\n{e}\n")
            raise

        nodes.append(node)
        num_successes += 1
    print()
    print(f"{num_successes=}")


def test_real_world():
    fn = "database.json"
    with open(fn, encoding="utf8") as database_file:
        db_json = database_file.read()
    database = Database.model_validate_json(db_json)

    messages = [m.content for m in database.message_table.get_rows()]
    test_valid_messages(messages)


def test_markdown_test_cases():
    fn = "markdown_test_cases.json"
    with open(fn, encoding="utf8") as fp:
        fixtures = json.load(fp)
    messages = [fixture["expected_output"] for fixture in fixtures["regular_tests"]]
    test_valid_messages(messages)

test_markdown_test_cases()
test_real_world()
