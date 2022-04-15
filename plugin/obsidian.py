import os
import json
from pathlib import Path
import webbrowser
import logging

logger = logging.getLogger(__name__)

VAULTS_FILE = 'obsidian.json'
VAULTS_PATH = Path(os.getenv('APPDATA'), 'obsidian', VAULTS_FILE)
CHECK_BOX = '- [ ]'
MARKED_CHECK_BOX = '- [x]'

def get_vaults():
    vaults = []
    try:
        with open(VAULTS_PATH, 'r', encoding='utf-8', errors='replace') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f'{VAULTS_PATH} not found!\nIs obsidian installed?')
        raise
    else:
        for vault in data['vaults'].keys():
            vaults.append(Vault(vault, data['vaults'][vault]))
        return vaults

def get_vault(id):
    try:
        with open(VAULTS_PATH, 'r', encoding='utf-8', errors='replace') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f'{VAULTS_PATH} not found!\nIs obsidian installed?')
        raise
    else:
        try:
            return Vault(id, data['vaults'][id])
        except KeyError:
            logger.error(f'{id} not found!')
            raise

def get_note(vault_id, note_path):
    vault = get_vault(vault_id)
    return Note(vault, note_path)


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

    def note(self, note_path):
        for note in self.notes():
            if str(note.relative_path) == note_path:
                return note


class Note(object):

    def __init__(self, vault: Vault, full_path: str):
        self.vault = vault
        self.path = full_path
        self.title = Path(full_path).name.replace('.md', '')
        self.relative_path = Path(str(full_path).replace(f'{self.vault.path}', ''))
        self.vault_path = f'{self.vault.name}{self.relative_path}'

    def open_note(self):
        open_note(self.vault.name, self.relative_path)

    def content(self):
        with open(self.path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()


    def toggle_checkbox(self, raw):
        content = self.content()
        for line in content.splitlines():
            if raw == line:
                if MARKED_CHECK_BOX in line:
                    toggled_line = line.replace(MARKED_CHECK_BOX, CHECK_BOX)
                else:
                    toggled_line = line.replace(CHECK_BOX, MARKED_CHECK_BOX)
                break
        content = content.replace(line, toggled_line)
        with open(self.path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(content)

    def checklists(self):
        checklists = []
        title = ''
        prev_line = ''
        for line in self.content().splitlines():
            if CHECK_BOX in line or MARKED_CHECK_BOX in line:
                description = line.replace(CHECK_BOX, '').replace(MARKED_CHECK_BOX, '').strip()
                if MARKED_CHECK_BOX in line:
                    checked = True
                else:
                    checked = False
                if (CHECK_BOX not in prev_line and MARKED_CHECK_BOX not in prev_line) and prev_line.endswith(':'):
                    title = prev_line.replace(':', '').strip()
                checklists.append(
                    {
                        'title': title,
                        'description': description,
                        'checked': checked,
                        'raw': line
                    }
                )
            else:
                title = ''
            prev_line = line
        return checklists




if __name__ == "__main__":
    vaults = get_vaults()
    for vault in vaults:
        for note in vault.notes():
            print(note.title)
            open_note(vault.name, str(note.relative_path))
            break