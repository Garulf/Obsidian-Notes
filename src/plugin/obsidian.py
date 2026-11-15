from __future__ import annotations

import json
import logging
import os
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)

VAULTS_FILE = "obsidian.json"
CHECK_BOX = "- [ ]"
MARKED_CHECK_BOX = "- [x]"


def vaults_path() -> Path:
    return Path(os.getenv("APPDATA") or "", "obsidian", VAULTS_FILE)


def _read_vaults() -> dict[str, dict]:
    path = vaults_path()
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)["vaults"]
    except FileNotFoundError:
        logger.error("%s not found! Is Obsidian installed?", path)
        raise


def get_vaults() -> list[Vault]:
    return [Vault(vault_id, data) for vault_id, data in _read_vaults().items()]


def get_vault(vault_id: str) -> Vault:
    vaults = _read_vaults()
    try:
        return Vault(vault_id, vaults[vault_id])
    except KeyError:
        logger.error("Vault %s not found!", vault_id)
        raise


def get_note(vault_id: str, note_path: str) -> Note:
    return Note(get_vault(vault_id), note_path)


def note_uri(vault_name: str, note_path: str) -> str:
    query = f"open?vault={vault_name}&file={note_path}"
    return "obsidian://" + query.replace(" ", "%20").replace("/", "%2F").replace("\\", "%2F")


def open_note(vault_name: str, note_path: str) -> None:
    webbrowser.open(note_uri(vault_name, note_path))


class Vault:

    def __init__(self, vault_id: str, data: dict):
        self.id = vault_id
        self.path: str = data["path"]
        self.name = Path(self.path).name

    def notes(self) -> list[Note]:
        notes = []
        for folder, subfolders, files in os.walk(self.path, followlinks=True):
            subfolders[:] = [name for name in subfolders if not name.startswith(".")]
            notes.extend(Note(self, os.path.join(folder, name)) for name in files if name.lower().endswith(".md"))
        return notes

    def note(self, note_path: str) -> Note | None:
        for note in self.notes():
            if str(note.relative_path) == note_path:
                return note
        return None


class Note:

    def __init__(self, vault: Vault, full_path: str | Path):
        self.vault = vault
        self.path = full_path
        self.title = Path(full_path).name.replace(".md", "")
        self.relative_path = Path(str(full_path).replace(vault.path, ""))
        self.vault_path = f"{vault.name}{self.relative_path}"

    def open_note(self) -> None:
        open_note(self.vault.name, str(self.relative_path))

    def content(self) -> str:
        with open(self.path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def toggle_checkbox(self, raw: str) -> None:
        content = self.content()
        if raw not in content.splitlines():
            return
        if MARKED_CHECK_BOX in raw:
            toggled = raw.replace(MARKED_CHECK_BOX, CHECK_BOX)
        else:
            toggled = raw.replace(CHECK_BOX, MARKED_CHECK_BOX)
        with open(self.path, "w", encoding="utf-8", errors="replace") as f:
            f.write(content.replace(raw, toggled))

    def checklists(self) -> list[dict]:
        checklists = []
        title = ""
        prev_line = ""
        for line in self.content().splitlines():
            if is_checkbox(line):
                if not is_checkbox(prev_line) and prev_line.endswith(":"):
                    title = prev_line.replace(":", "").strip()
                checklists.append({
                    "title": title,
                    "description": line.replace(CHECK_BOX, "").replace(MARKED_CHECK_BOX, "").strip(),
                    "checked": MARKED_CHECK_BOX in line,
                    "raw": line,
                })
            else:
                title = ""
            prev_line = line
        return checklists


def is_checkbox(line: str) -> bool:
    return CHECK_BOX in line or MARKED_CHECK_BOX in line
