import asyncio

import notes
from launcher import KEEP_OPEN


def call(method, *params):
    return asyncio.run(notes.plugin._event_handler.trigger_event(method, *params))


def results(method, *params):
    return call(method, *params)["Result"]


def test_empty_query_lists_every_note(vaults):
    titles = sorted(result["Title"] for result in results("query", ""))
    assert titles == ["Garden Plan", "Meeting Notes", "Shopping List"]


def test_query_scores_the_best_match_highest(vaults):
    found = sorted(results("query", "shopping"), key=lambda result: -result["Score"])
    assert found[0]["Title"] == "Shopping List"
    assert found[0]["Score"] == notes.match("shopping", "Shopping List")
    assert all(result["Score"] < found[0]["Score"] for result in found[1:])


def test_a_note_containing_the_query_beats_a_short_unrelated_title(vaults):
    (vaults["work"] / "ToDo.md").write_text("", encoding="utf-8")
    (vaults["work"] / "After Effects tips and shortcuts.md").write_text("", encoding="utf-8")
    found = sorted(results("query", "tips"), key=lambda result: -result["Score"])
    assert [result["Title"] for result in found] == ["After Effects tips and shortcuts"]


def test_query_drops_notes_that_do_not_match(vaults):
    assert results("query", "qqq") == []


def test_query_matches_the_path_inside_the_vault(vaults):
    found = {result["Title"]: result["Score"] for result in results("query", "personal/projects")}
    assert "Garden Plan" in found
    assert found["Garden Plan"] > 0


def test_note_result_opens_the_note_in_its_vault(vaults, keyword):
    (result,) = results("query", "garden plan")
    assert result["SubTitle"] == "Personal/Projects/Garden Plan.md"
    assert result["IcoPath"] == notes.ICON
    assert result["AutoCompleteText"] == "ob Garden Plan"
    assert result["Preview"]["Description"] == "Personal/Projects/Garden Plan.md"
    assert result["JsonRPCAction"] == {
        "Method": "open_note",
        "Parameters": ["Personal", "/Projects/Garden Plan.md"],
        "DontHideAfterAction": False,
    }
    assert result["ContextData"] == [
        "a1b2c3d4e5f60718",
        str(vaults["personal"] / "Projects" / "Garden Plan.md"),
    ]


def test_autocomplete_without_a_keyword_is_the_title(vaults):
    (result,) = results("query", "garden plan")
    assert result["AutoCompleteText"] == "Garden Plan"


def test_missing_obsidian_config_says_so(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    (result,) = results("query", "anything")
    assert result["Title"] == "Obsidian not found"
    assert result["SubTitle"] == "Please install Obsidian"


def test_open_note_action(opened):
    call("open_note", "Personal", "/Projects/Garden Plan.md")
    assert opened == ["obsidian://open?vault=Personal&file=%2FProjects%2FGarden%20Plan.md"]


def test_context_menu_lists_checklist_items(vaults):
    path = str(vaults["personal"] / "Shopping List.md")
    menu = results("context_menu", ["a1b2c3d4e5f60718", path])
    assert [(item["Title"], item["SubTitle"], item["Glyph"]["Glyph"]) for item in menu] == [
        ("Oat milk", "Groceries", notes.CHECK_BOX_GLYPH),
        ("Coffee beans", "Groceries", notes.MARKED_CHECK_BOX_GLYPH),
        ("Sourdough", "Groceries", notes.CHECK_BOX_GLYPH),
        ("Return bottles", "", notes.CHECK_BOX_GLYPH),
    ]
    assert menu[0]["Glyph"]["FontFamily"] == "/Resources/#Segoe Fluent Icons"
    assert menu[0]["JsonRPCAction"] == {
        "Method": "toggle_checkbox",
        "Parameters": ["a1b2c3d4e5f60718", path, "- [ ] Oat milk"],
        "DontHideAfterAction": True,
    }


def test_context_menu_without_note_data_is_empty(vaults):
    assert results("context_menu", None) == []


def test_toggle_checkbox_keeps_the_window_open(vaults):
    path = vaults["personal"] / "Shopping List.md"
    assert call("toggle_checkbox", "a1b2c3d4e5f60718", str(path), "- [ ] Sourdough") == KEEP_OPEN
    assert "- [x] Sourdough" in path.read_text(encoding="utf-8")


def test_errors_are_shown_as_a_result(vaults):
    (result,) = results("context_menu", ["deleted-vault", "/nowhere.md"])
    assert result["Title"] == "KeyError"
