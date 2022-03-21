from difflib import SequenceMatcher as SM

from flox import Flox

import obsidian

CHECK_BOX_GLYPH = '\ue003'
MARKED_CHECK_BOX_GLYPH = '\ue005'


def match(query, match):
    return int(SM(lambda x: x == " ", query.lower().replace('\\', ' '), match.lower().replace('\\', ' '), autojunk=False).ratio() * 100)

class Obsidian(Flox):

    def query(self, query):
        try:
            vaults = obsidian.get_vaults()
        except FileNotFoundError:
            self.add_item(
                title='Obsidian not found',
                subtitle='Please install Obsidian',
            )
            return
        for vault in vaults:
            for note in vault.notes():
                title_score = match(query, note.title)
                subtitle_score = match(query, str(note.vault_path))
                score = max(title_score, subtitle_score)
                if score > 20 or query == '':
                    self.add_item(
                        title=note.title,
                        subtitle=str(note.vault_path),
                        icon=self.icon,
                        method=self.open_note,
                        parameters=[vault.name, str(note.relative_path)],
                        score=score,
                        context=[vault.id, str(note.path), note.checklists()]
                    )

    def context_menu(self, data):
        vault_id = data[0]
        note_path = data[1]
        for checks in data[2]:
            self.add_item(
                title=checks['description'],
                subtitle=checks['title'],
                glyph=MARKED_CHECK_BOX_GLYPH if checks['checked'] else CHECK_BOX_GLYPH,
                method=self.toggle_checkbox,
                parameters=[vault_id, note_path, checks['raw']],
                dont_hide=True
            )

    def toggle_checkbox(self, vault_id, note_path, raw):
        note = obsidian.get_note(vault_id, note_path)
        note.toggle_checkbox(raw)


    def open_note(self, vault_name, note_path):
        obsidian.open_note(vault_name, note_path)

if __name__ == "__main__":
    Obsidian()
