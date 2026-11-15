import obsidian
import pytest


def test_vaults_are_read_from_obsidian_config(vaults):
    found = {vault.id: vault for vault in obsidian.get_vaults()}
    assert set(found) == {"a1b2c3d4e5f60718", "0f1e2d3c4b5a6978"}
    personal = found["a1b2c3d4e5f60718"]
    assert personal.name == "Personal"
    assert personal.path == str(vaults["personal"])


def test_missing_config_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        obsidian.get_vaults()


def test_unknown_vault_raises_key_error(vaults):
    with pytest.raises(KeyError):
        obsidian.get_vault("missing")


def test_notes_lists_markdown_files_recursively(vaults):
    vault = obsidian.get_vault("a1b2c3d4e5f60718")
    titles = sorted(note.title for note in vault.notes())
    assert titles == ["Garden Plan", "Shopping List"]


def test_note_paths_are_relative_to_the_vault(vaults):
    vault = obsidian.get_vault("a1b2c3d4e5f60718")
    note = vault.note("/Projects/Garden Plan.md")
    assert note is not None
    assert note.vault_path == "Personal/Projects/Garden Plan.md"
    assert vault.note("/Nope.md") is None


def test_note_uri_encodes_spaces_and_separators():
    uri = obsidian.note_uri("My Vault", "\\Projects\\Garden Plan.md")
    assert uri == "obsidian://open?vault=My%20Vault&file=%2FProjects%2FGarden%20Plan.md"


def test_open_note_opens_the_obsidian_uri(opened):
    obsidian.open_note("Personal", "/Shopping List.md")
    assert opened == ["obsidian://open?vault=Personal&file=%2FShopping%20List.md"]


def test_checklists_group_items_under_their_heading(vaults):
    note = obsidian.get_note("a1b2c3d4e5f60718", str(vaults["personal"] / "Shopping List.md"))
    assert note.checklists() == [
        {"title": "Groceries", "description": "Oat milk", "checked": False, "raw": "- [ ] Oat milk"},
        {"title": "Groceries", "description": "Coffee beans", "checked": True, "raw": "- [x] Coffee beans"},
        {"title": "Groceries", "description": "Sourdough", "checked": False, "raw": "- [ ] Sourdough"},
        {"title": "", "description": "Return bottles", "checked": False, "raw": "- [ ] Return bottles"},
    ]


def test_toggle_checkbox_flips_one_item(vaults):
    path = vaults["personal"] / "Shopping List.md"
    note = obsidian.get_note("a1b2c3d4e5f60718", str(path))
    note.toggle_checkbox("- [ ] Oat milk")
    note.toggle_checkbox("- [x] Coffee beans")
    text = path.read_text(encoding="utf-8")
    assert "- [x] Oat milk" in text
    assert "- [ ] Coffee beans" in text
    assert "- [ ] Sourdough" in text


def test_toggle_checkbox_ignores_a_line_that_is_gone(vaults):
    path = vaults["personal"] / "Shopping List.md"
    before = path.read_text(encoding="utf-8")
    obsidian.get_note("a1b2c3d4e5f60718", str(path)).toggle_checkbox("- [ ] Not there")
    assert path.read_text(encoding="utf-8") == before


def test_unreadable_bytes_are_replaced(vaults):
    path = vaults["work"] / "Meeting Notes.md"
    path.write_bytes(b"- [ ] Caf\xe9 order\n")
    note = obsidian.get_note("0f1e2d3c4b5a6978", str(path))
    assert note.checklists()[0]["description"] == "Caf� order"
