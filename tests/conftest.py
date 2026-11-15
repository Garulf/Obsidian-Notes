import json

import notes
import pytest

SHOPPING_LIST = """# Shopping List

Groceries:
- [ ] Oat milk
- [x] Coffee beans
- [ ] Sourdough

Notes about the store.
- [ ] Return bottles
"""


@pytest.fixture
def vaults(tmp_path, monkeypatch):
    personal = tmp_path / "Documents" / "Personal"
    work = tmp_path / "Documents" / "Work"
    (personal / "Projects").mkdir(parents=True)
    (personal / ".obsidian").mkdir()
    work.mkdir(parents=True)
    (personal / "Shopping List.md").write_text(SHOPPING_LIST, encoding="utf-8")
    (personal / "Projects" / "Garden Plan.md").write_text("Raised beds along the fence.\n", encoding="utf-8")
    (personal / "Projects" / "image.png").write_bytes(b"\x89PNG")
    (work / "Meeting Notes.md").write_text("- [ ] Send agenda\n", encoding="utf-8")

    appdata = tmp_path / "AppData" / "Roaming"
    config_dir = appdata / "obsidian"
    config_dir.mkdir(parents=True)
    config = {
        "vaults": {
            "a1b2c3d4e5f60718": {"path": str(personal), "ts": 1730000000000, "open": True},
            "0f1e2d3c4b5a6978": {"path": str(work), "ts": 1730000000001},
        }
    }
    (config_dir / "obsidian.json").write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setenv("APPDATA", str(appdata))
    return {"personal": personal, "work": work}


@pytest.fixture
def keyword():
    launcher = notes.plugin.launcher
    launcher.action_keyword = "ob"
    yield launcher
    launcher.action_keyword = ""


@pytest.fixture
def opened(monkeypatch):
    uris = []
    monkeypatch.setattr("obsidian.webbrowser.open", uris.append)
    return uris
