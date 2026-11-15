from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from pyflowlauncher import Plugin, Result
from pyflowlauncher.models.result import Glyph, PreviewInfo
from pyflowlauncher.string_matcher import string_matcher

import obsidian
from launcher import KEEP_OPEN, ObsidianLauncher

logger = logging.getLogger(__name__)

ICON = str(Path(__file__).resolve().parent.parent / "icon.png")
GLYPH_FONT = "/Resources/#Segoe Fluent Icons"
CHECK_BOX_GLYPH = "\ue003"
MARKED_CHECK_BOX_GLYPH = "\ue005"

plugin = Plugin(launcher=ObsidianLauncher())


def match(query: str, text: str) -> int:
    result = string_matcher(query.replace("\\", " "), text.replace("\\", " "))
    return result.score if result.matched else 0


def make_result(title: str, subtitle: str = "", **kwargs) -> Result:
    preview = PreviewInfo(PreviewImagePath=None, Description=subtitle, IsMedia=False, PreviewDeligate=None)
    return Result(title=title, subtitle=subtitle, icon=ICON, preview=preview, **kwargs)


def autocomplete(title: str) -> str:
    keyword = plugin.launcher.action_keyword
    if keyword and keyword != "*":
        return f"{keyword} {title}"
    return title


@plugin.on_method
async def query(query: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, search, query)


def search(query: str) -> list[Result]:
    try:
        vaults = obsidian.get_vaults()
    except FileNotFoundError:
        return [make_result("Obsidian not found", "Please install Obsidian")]
    results = []
    for vault in vaults:
        for note in vault.notes():
            score = max(match(query, note.title), match(query, str(note.vault_path)))
            if score or query == "":
                results.append(note_result(vault, note, score))
    return results


def note_result(vault: obsidian.Vault, note: obsidian.Note, score: int) -> Result:
    return make_result(
        note.title,
        str(note.vault_path),
        score=score,
        context_data=[vault.id, str(note.path)],
        auto_complete_text=autocomplete(note.title),
    ).add_action(open_note, [vault.name, str(note.relative_path)])


@plugin.on_method
def context_menu(data: list | None):
    if not data or len(data) < 2:
        return []
    vault_id, note_path = data[0], data[1]
    note = obsidian.get_note(vault_id, note_path)
    return [checklist_result(vault_id, note_path, item) for item in note.checklists()]


def checklist_result(vault_id: str, note_path: str, item: dict) -> Result:
    glyph = MARKED_CHECK_BOX_GLYPH if item["checked"] else CHECK_BOX_GLYPH
    return make_result(
        item["description"],
        item["title"],
        glyph=Glyph(Glyph=glyph, FontFamily=GLYPH_FONT),
    ).add_action(toggle_checkbox, [vault_id, note_path, item["raw"]], dont_hide_after_action=True)


@plugin.on_method
def toggle_checkbox(vault_id: str, note_path: str, raw: str):
    obsidian.get_note(vault_id, note_path).toggle_checkbox(raw)
    return KEEP_OPEN


@plugin.on_method
def open_note(vault_name: str, note_path: str):
    obsidian.open_note(vault_name, note_path)


@plugin.on_except(Exception)
def show_error(error: Exception):
    logger.exception("Obsidian Notes failed", exc_info=error)
    return make_result(type(error).__name__, str(error))
