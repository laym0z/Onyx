import configparser
from pathlib import Path

VAULTS_FOLDER = Path("Vaults")
CONFIG_FILE = "config.ini"


def create_config(vault: Path):
    config = configparser.ConfigParser()

    config['PLACEHOLDERS'] = {
        'MENU_PLACEHOLDER_NAME': "<div class='PLACEHODER'></div>",
        'MAIN_CONTENT_PLACEHOLDER': '"<div class="CONTENT-PLACEHODER"></div>"'
    }
    config['ROOT_FILES'] = {
        'ROOT_MD': 'index.md',
        'ROOT_HTML': 'index.html',
        'ROOT_CSS': 'assets/styles/style.css',
        'ROOT_JS': 'assets/script.js'
    }

    config['DEFAULT_PATHES'] = {
        'PATH_TO_IMAGES': 'images/',
        'PATH_TO_FOLDER_ICON': 'assets/icons/folder.png',
        'PATH_TO_FAVICON': 'assets/icons/favicon.ico',
    }

    config['BLACKLIST'] = {
        'blacklist_files': ["images", "style.css", "assets", "script.js"]
    }

    with open(vault/CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def read_config(vault: Path):
    config = configparser.ConfigParser()
    config.read(VAULTS_FOLDER/vault/CONFIG_FILE)
    config_storage = {
        'PATH_TO_IMAGES': config.get('DEFAULT_PATHES', 'PATH_TO_IMAGES'),
        'PATH_TO_FOLDER_ICON': config.get('DEFAULT_PATHES', 'PATH_TO_FOLDER_ICON'),
        'PATH_TO_FAVICON': config.get('DEFAULT_PATHES', 'PATH_TO_FAVICON'),

        'ROOT_MD': config.get('ROOT_FILES', 'ROOT_MD'),
        'ROOT_HTML': config.get('ROOT_FILES', 'ROOT_HTML'),
        'ROOT_CSS': config.get('ROOT_FILES', 'ROOT_CSS'),
        'ROOT_JS': config.get('ROOT_FILES', 'ROOT_JS'),

        'MENU_PLACEHOLDER_NAME': config.get('PLACEHOLDERS', 'MENU_PLACEHOLDER_NAME'),
        'MAIN_CONTENT_PLACEHOLDER': config.get('PLACEHOLDERS', 'MAIN_CONTENT_PLACEHOLDER'),

        'blacklist_files': config.get('BLACKLIST', 'blacklist_files')
    }
    return config_storage

def get_vault():
    return VAULTS_FOLDER

def get_config_file():
    return CONFIG_FILE