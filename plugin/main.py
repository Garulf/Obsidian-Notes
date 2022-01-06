from difflib import SequenceMatcher as SM

from flox import Flox

import obsidian

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
                        method=self.open_note,
                        parameters=[vault.name, str(note.relative_path)],
                        score=score,
                    )

    def context_menu(self, data):
        pass

    def open_note(self, vault_name, note_path):
        obsidian.open_note(vault_name, note_path)

if __name__ == "__main__":
    Obsidian()
