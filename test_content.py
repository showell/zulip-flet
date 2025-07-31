import json
import sys

sys.path.append("api")
from api.database import Database
from api.message_parser import get_zulip_content


def test_valid_messages(messages, label):
    num_successes = 0
    for html in messages:
        try:
            node = get_zulip_content(html)
            node.as_text()
            node.as_html()
        except Exception as e:
            print("---")
            print(f"\nOUTER HMTL:\n{repr(html)}")
            print(f"\nERROR:\n{e}\n")
            raise

        num_successes += 1
    print()
    print(f"{num_successes=} from {label}")


def test_custom_test_cases():
    messages = [
        '<p><span class="user-mention channel-wildcard-mention" data-user-id="*">@all</span></p>',
        '<p><span class="user-mention channel-wildcard-mention" data-user-id="*">@everyone</span></p>',
        '<p><span class="user-mention channel-wildcard-mention" data-user-id="*">@channel</span></p>',
        '<p><span class="topic-mention">@topic</span></p>',
        '<p><span class="user-mention channel-wildcard-mention silent" data-user-id="*">all</span></p>',
        '<p><span class="user-mention channel-wildcard-mention silent" data-user-id="*">everyone</span></p>',
        '<p><span class="user-mention channel-wildcard-mention silent" data-user-id="*">channel</span></p>',
        '<p><span class="topic-mention silent">topic</span></p>',
        '<p><a href="https://chat.zulip.org/user_uploads/2/ba/JW9YL_kxk6GjYn2CwTzUoz6k/한국어-파일.txt">한국어 파일.txt</a></p>',
        '<div class="message_embed">'
        + '<a class="message_embed_image" href="https://pub-14f7b5e1308d42b69c4a46608442a50c.r2.dev/image+title+description.html" style="background-image: url(&quot;https://uploads.zulipusercontent.net/98fe2fe&quot;)"></a>'
        + '<div class="data-container">'
        + '<div class="message_embed_title"><a href="https://pub-14f7b5e1308d42b69c4a46608442a50c.r2.dev/image+title+description.html" title="Zulip — organized team chat">Zulip — organized team chat</a></div>'
        + '<div class="message_embed_description">Zulip is an organized team chat app for distributed teams of all sizes.</div></div></div>',
    ]
    test_valid_messages(messages, "custom")


def test_real_world():
    fn = "database.json"
    try:
        with open(fn, encoding="utf8") as database_file:
            db_json = database_file.read()
    except FileNotFoundError:
        print("""
            ERROR: can't find database.json!!!!

            Try running python .\\api\\data_layer.py
        """)
        raise

    database = Database.model_validate_json(db_json)

    messages = [m.content for m in database.message_table.get_rows()]
    test_valid_messages(messages, "real world")


def test_markdown_test_cases():
    fn = "markdown_test_cases.json"
    with open(fn, encoding="utf8") as fp:
        fixtures = json.load(fp)
    messages = [fixture["expected_output"] for fixture in fixtures["regular_tests"]]
    test_valid_messages(messages, "markdown_test_cases.json (from Zulip)")


test_custom_test_cases()
test_markdown_test_cases()
test_real_world()
