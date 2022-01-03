import os
import json
from pathlib import Path
import webbrowser

VAULTS_FILE = 'obsidian.json'
VAULTS_PATH = Path(os.getenv('APPDATA'), 'obsidian', VAULTS_FILE)

def get_vaults():
    vaults = []
    with open(VAULTS_PATH, 'r') as f:
        data = json.load(f)
    for vault in data['vaults'].keys():
        vaults.append(Vault(vault, data['vaults'][vault]))
    return vaults

def open_note(vault_name, note_path):
    URI = f'open?vault={vault_name}&file={note_path}'.replace(' ', '%20').replace('/', '%2F').replace('\\', '%2F')
    URI = f'obsidian://{URI}'
    webbrowser.open(URI)

class Vault(object):

    def __init__(self, id:str, vault: dict):
        self._data = vault
        self.id = id
        self.name = Path(vault['path']).name
        for key, value in vault.items():
            setattr(self, key, value)

    def notes(self):
        notes = []
        for note in Path(self.path).glob('**/*.md'):
            notes.append(Note(self, note))
        return notes


class Note(object):

    def __init__(self, vault: Vault, full_path: str):
        self.vault = vault
        self.path = full_path
        self.title = Path(full_path).name.replace('.md', '')
        self.relative_path = Path(str(full_path).replace(f'{self.vault.path}', ''))
        self.vault_path = f'{self.vault.name}{self.relative_path}'

    def open_note(self):
        open_note(self.vault.name, self.relative_path)

if __name__ == "__main__":
    vaults = get_vaults()
    for vault in vaults:
        for note in vault.notes():
            print(note.title)
            open_note(vault.name, str(note.relative_path))
            break
