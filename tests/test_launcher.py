import io
import json

import notes
from launcher import KEEP_OPEN, ObsidianLauncher


def test_keep_open_reply_is_sent_as_is():
    launcher = ObsidianLauncher()
    sent = []
    launcher._client.send = sent.append
    launcher._send_response(7, "toggle_checkbox", KEEP_OPEN)
    launcher._send_response(8, "open_note", None)
    assert sent == [
        {"id": 7, "result": {"hide": False}, "error": None},
        {"id": 8, "result": {}, "error": None},
    ]


def run_plugin(monkeypatch, *requests):
    lines = "".join(json.dumps(request) + "\n" for request in requests)
    stdout = io.StringIO()
    monkeypatch.setattr("sys.stdin", io.StringIO(lines))
    monkeypatch.setattr("sys.stdout", stdout)
    notes.plugin.run()
    return {reply["id"]: reply for reply in map(json.loads, stdout.getvalue().splitlines())}


def test_json_rpc_query_round_trip(vaults, monkeypatch):
    replies = run_plugin(
        monkeypatch,
        {"id": 1, "method": "initialize", "params": [{}]},
        {"id": 2, "method": "query", "params": [{"search": "shopping list", "actionKeyword": "notes"}, {}]},
        {"id": 3, "method": "close", "params": []},
    )
    assert notes.plugin.launcher.action_keyword == "notes"
    result = max(replies[2]["result"]["result"], key=lambda result: result["Score"])
    assert result["Title"] == "Shopping List"
    assert result["AutoCompleteText"] == "notes Shopping List"
    notes.plugin.launcher.action_keyword = ""


def test_json_rpc_toggle_checkbox_stays_open(vaults, monkeypatch):
    path = str(vaults["personal"] / "Shopping List.md")
    replies = run_plugin(
        monkeypatch,
        {"id": 1, "method": "toggle_checkbox", "params": [["a1b2c3d4e5f60718", path, "- [ ] Oat milk"]]},
        {"id": 2, "method": "close", "params": []},
    )
    assert replies[1]["result"] == {"hide": False}
