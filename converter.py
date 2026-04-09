import markdown
import re
from os import path, remove, rmdir, mkdir
from pathlib import Path
from PIL import Image
import sys
import shutil
from tabulate import tabulate
import hashlib
import json
import configparser

#TODO: REWRITE THIS WHOLE SHITCODE, HOLY FUCK

#TODO: CREATE TEMPLATES HTML?

#TODO: TRACK ASSETS FOLDER CHANGES

#--------------------------GONFIG SECTION-----------------------

ARGS = {
    "--help": "print help menu",
    "--src": "source directory (--src [PATH])",
    "--dst": "destination directory (--dst [PATH])",
    # "--ri": "write or rewrite main page",
    "--rc": "write or rewrite style.css "
}
blacklist_menu = ["images", "style.css", "assets", "script.js"]

CONFIG_FILE = "config.ini"

VAULTS_FOLDER = Path("Vaults")

config_storage = {}

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
    
#---------------CREATE MAIN WEB COMPONENTS----------------------

def create_css(dst: Path):
    with open(Path(config_storage['ROOT_CSS']), "r") as css:
        css_text = css.read()
    with open(dst / Path(config_storage['ROOT_CSS']), "w") as f:
        f.write(css_text)

def create_root(dst: Path, vault_folder: Path):
    if path.exists(vault_folder/"index.md"):
        with open(vault_folder/"index.md", "r", encoding="utf-8") as index:
            text = index.read()
            md_to_html = markdown.markdown(text,extensions=["fenced_code"])
    else:
        with open(vault_folder/"index.md", "w", encoding="utf-8") as index:
            text = f"This is the main page. You can change its content in the `Vaults/{path.basename(vault_folder)}/index.md`"
            index.write(text)
            md_to_html = markdown.markdown(text, extensions=["fenced_code"])
    html_content = f"""
        <!DOCTYPE html>
        <html lang="uk">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Main Page</title>
            <link rel="stylesheet" href="{Path(config_storage['ROOT_CSS'])}">
            <link rel="icon" href="{Path(config_storage['PATH_TO_FAVICON'])}" type="image/x-icon">
        </head>
        <body>
            
            <div class="main">
                <div class='PLACEHODER'></div>
                <div class="content">
                    {md_to_html}
                </div>
            </div>
            
        </body>
        <footer>
            <p>Created with <a href="https://github.com/laym0z/Onyx">Onyx</a> by <a href=https://github.com/laym0z>laym0z</a></p>
        </footer>
        <script src="{Path(config_storage['ROOT_JS'])}"></script>
        </html>
    """
    with open(dst / Path(config_storage['ROOT_HTML']), "w", encoding="utf-8") as index:
        index.write(html_content)

def create_js(dst: Path):
    with open(Path(config_storage['ROOT_JS']), "r") as index:
        text = index.read()
    with open(dst / Path(config_storage['ROOT_JS']), "w") as index:
        index.write(text)   

#-----------------------JSON VAULT------------------------------

def generate_json(src_vault: Path) -> dict:
    tree = {src_vault.name: {}}
    for sub_path in src_vault.rglob("*"):
        if any(part.startswith('.') for part in sub_path.parts):
            continue
        rel = sub_path.relative_to(src_vault)
        parts = rel.parts

        node = tree[src_vault.name]

        for part in parts[:-1]:
            node = node.setdefault(part, {})

        name = parts[-1]

        if sub_path.is_dir():
            node.setdefault(name, {})
        else:
            node[name] = file_hash(sub_path)
    return tree

def flatten(tree, prefix=""):
    files = {}
    dirs = []
    for name, value in tree.items():
        current_path = f"{prefix}/{name}" if prefix else name

        if isinstance(value, dict):
            # This is dir
            dirs.append(current_path)

            sub_files, sub_dirs = flatten(value, current_path)
            files.update(sub_files)
            dirs.extend(sub_dirs)
        else:
            # This is file
            files[current_path] = value

    return files, dirs

#----------------------FILES AND DIRS---------------------------

def file_hash(path: Path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def delete_dirs_and_files(remove_files: dict, remove_dirs: dict, dst: Path):
    for value in remove_files:
        new_name = path.splitext(value)[0]+'.html'
        # file_name = path.basename(new_name)
        new_path = Path(dst/new_name)
        if not new_path.is_dir():
            remove(new_path)
        else:
            pass
    for value in remove_dirs:
        path_obj = Path(value)
        new_path = Path(dst/path_obj)
        try:
            shutil.rmtree(new_path, ignore_errors=True)
        except:
            continue

#-----------------------NAVIGATION MENU-----------------------------------
def set_menu(sub_path: Path, dst_path: Path, folder_id_counter: int, dst_folder: Path) -> str:
    home_page = ""
    html = "<ul class='sub-list'>\n"

    for item in sorted(dst_path.iterdir()):
        if item.name.startswith('.') or item.name in config_storage['blacklist_files']:
            continue
        if item.name == config_storage['ROOT_HTML']:
            new_name = "HOME"
        else: new_name = item.stem
        
        target_path = item.with_name(item.name)
        if not sub_path.is_dir(): 
            sub_path = sub_path.parent
        relative_path = path.relpath(target_path, start=sub_path)
        relative_path = relative_path.replace("\\", "/")

        folder_id_counter+=1

        assets_path = path.relpath(dst_folder/Path(config_storage['PATH_TO_FOLDER_ICON']), start=sub_path)

        if item.is_dir():
            html += f"<li class='folder' data-folderID='{folder_id_counter}'><strong class='folder-name'><img src='{assets_path}'>{new_name}</strong>\n"
            html += set_menu(sub_path, item, folder_id_counter, dst_folder)
            html += "</li>\n"
        else:
            if item.name == config_storage['ROOT_HTML']:
                home_page = f'<h1 class="home"><a href="{relative_path}">{new_name}</a></h1>\n'
            else:
                html += f'<li class="file"><a href="{relative_path}">{new_name}</a></li>\n'

    html += "</ul>\n"
    return home_page+html

def create_menu(dst_path: Path):
    for sub_path in dst_path.rglob("*"):
        if any(part.startswith('.') for part in sub_path.parts):
            continue
        if not sub_path.is_dir():
            # print(path.name)
            if sub_path.suffix == ".html":
                with open(sub_path, "r", encoding="utf-8") as html:
                    data = html.read()
                with open(sub_path, "w", encoding="utf-8") as html:
                    folder_id_counter = 0
                    data = data.replace(config_storage['MENU_PLACEHOLDER_NAME'], f"<div class='menu'>{set_menu(sub_path, dst_path, folder_id_counter, dst_path)}</div>")
                    # html.write(set_menu(path, root_path))
                    html.write(data)            
 
#---------------------------CONVERT------------------------------------

def make_changes(tree: dict, vault_path: Path, src_vault: Path, dst_path: Path):
    with open(vault_path, "r", encoding="utf-8") as f:
        old_json = json.load(f)

        new_files, new_dirs = flatten(tree[src_vault.name])
        old_files, old_dirs = flatten(old_json[src_vault.name])
        new_files_keys = set(new_files)
        old_files_keys = set(old_files)

        new_dirs_keys = set(new_dirs)
        old_dirs_keys = set(old_dirs)

        #--------------FILES-------------------
        added_files = new_files_keys - old_files_keys

        removed_files = old_files_keys - new_files_keys

        changed_files = {
            k for k in new_files_keys & old_files_keys
            if new_files[k] != old_files[k]
        }

        #-------------DIRS----------------------

        added_dirs = new_dirs_keys - old_dirs_keys

        removed_dirs = old_dirs_keys - new_dirs_keys

    #-------------------------------------
        if removed_files or removed_dirs:
            delete_dirs_and_files(removed_files, removed_dirs, dst_path)
            if removed_files:
                print(f"Removed files: {removed_files}")
            if removed_dirs:
                print(f"Removed folders: {removed_dirs}")
        if added_files or added_dirs or changed_files:
            if changed_files:
                print(f"Changed files: {changed_files}")
            if added_files:
                print(f"Added files: {added_files}")
            if added_dirs:
                print(f"Added folders: {added_dirs}")
        copy_directory(src_vault, dst_path)
        print(f"Changes has been stored: {vault_path}")


def copy_directory(src_path: Path, dst_path: Path):
    image_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".svg",
        ".ico"
    ]
    for sub_path in src_path.rglob("*"):
        if any(part.startswith('.') for part in sub_path.parts):
            continue

        relative = sub_path.relative_to(src_path)
        target = dst_path / relative
        
        if sub_path.is_dir():
            target.mkdir(parents=True, exist_ok=True)

        elif sub_path.suffix == ".md":
            target = target.with_suffix(".html")
            target.parent.mkdir(parents=True, exist_ok=True)

            with open(sub_path, "r", encoding="utf-8") as f:
                text = f.read()

            blockquote = note_blocks(text)
            photos = set_photos(blockquote, target, dst_path)

            md_to_html = markdown.markdown(photos,extensions=["fenced_code", "extra"])
            html_content = f"""
                <!DOCTYPE html>
                <html lang="uk">
                    <head>
                        <meta charset="UTF-8">
                        <title>{target.stem}</title>
                        <link rel="stylesheet" href={path.relpath(dst_path / Path(config_storage['ROOT_CSS']), target.parent)}>
                        <link rel="icon" href={path.relpath(dst_folder/Path(config_storage['PATH_TO_FAVICON']), target.parent)} type="image/x-icon">
                    </head>
                    <body>
                        
                        <div class="main">
                            {config_storage['MENU_PLACEHOLDER_NAME']}
                            <div class="content">
                            <h1 class="topic-name">{target.stem}</h2>
                            {md_to_html}
                            </div>
                        </div>
                    </body>
                    <footer>
                        <p>Created with <a href="https://github.com/laym0z/Onyx">Onyx</a> by <a href=https://github.com/laym0z>laym0z</a></p>
                    </footer>
                    <script src={path.relpath(dst_path / Path(config_storage['ROOT_JS']), target.parent)}></script>
                </html>
                """
            # print(target.name)
            with open(target, "w", encoding="utf-8") as f:
                f.write(html_content)

        elif sub_path.suffix in image_extensions:
            img = Image.open(sub_path)
            img.save(target)
    if not Path(VAULTS_FOLDER).is_dir():
        Path(config_storage['DEFAULT_JSON_FOLDER']).mkdir(parents=True, exist_ok=True)

#---------------------------STYLING------------------------------------

def set_photos(html: str, current_path: Path, dst_path: Path) -> str:
    pattern = re.compile(r'!\[\[(.+?)\]\]')

    def replacer(match):
        filename = match.group(1).strip()
        image_path = path.join(path.relpath(dst_path / Path(config_storage['PATH_TO_IMAGES']), current_path.parent), filename)
        
        return f'<div class="image-div"><img src="{image_path}" alt="{filename}" /></div>'

    return pattern.sub(replacer, html)

def note_blocks(md_text: str) -> str:
    pattern = re.compile(
        r'(?:^>?\s*)\[!(note|warning|tip|info|danger|example|success|question)\]\s*(.*)', 
        flags=re.IGNORECASE
    )

    def replacer(match):
        callout_type = match.group(1).lower()
        content = match.group(2).strip()
        return f'<div class="callout callout-{callout_type}" markdown="1">{content}</div>'

    processed_lines = []
    for line in md_text.split("\n"):
        processed_lines.append(pattern.sub(replacer, line))

    return "\n".join(processed_lines)

#-------------------HELP---------------

def print_help():
    list = []
    for key, value in ARGS.items():
        list.append([key, value])
    print(tabulate(list))

#------------------MAIN----------------

if __name__ == "__main__":
    CREATE_CSS = False
    # CREATE_HTML = False
    arguments = []
    for arg in sys.argv[1:]:
        arguments.append(arg)
    if len(arguments) == 0 or (len(arguments) == 1 and arguments[0] != "--help"):
        print_help()
    elif arguments[0] == "--help":
        print_help()
    elif not "--src" in arguments: 
        print("Please, provide the obsidian vault with '--src VAULT'")
    else:
        i = 0
        for arg in arguments:
            if arg == "--src":
                try:
                    src_vault = Path(arguments[i+1])
                    if not src_vault.exists():
                        print(f"Provided source path does not exist: {src_vault}")
                        sys.exit()
                except:
                    print_help()
                    sys.exit()
            elif arg == "--dst":
                try:
                    dst_folder = Path(arguments[i+1])
                except:
                    print(f"Path is invalid")
                    print_help()
                    sys.exit()
            # elif arg == "--ri":
            #     CREATE_HTML=True
            elif arg == "--rc":
                CREATE_CSS=True
            
            i+=1

        #-------------CONFIG-------------------
        src_dir_name = path.basename(src_vault)
        if not path.exists(VAULTS_FOLDER/src_dir_name/CONFIG_FILE):
            create_config(Path(VAULTS_FOLDER/src_dir_name))
            print("Config file has been created!")

        config_storage = read_config(Path(src_dir_name))
        #Generate new json 
        tree = generate_json(src_vault)
        new_json = json.dumps(tree, indent=4)

        
        vault_path_to_json = VAULTS_FOLDER/src_dir_name/f"{src_dir_name}.json"

        if path.exists(vault_path_to_json):
            make_changes(tree, vault_path_to_json, src_vault, dst_folder)
            with open(vault_path_to_json, "w", encoding="utf-8") as f:
                f.write(json.dumps(tree, indent=4))
        else:
            if not path.exists(VAULTS_FOLDER/src_dir_name):
                mkdir(VAULTS_FOLDER/src_dir_name)
            with open(vault_path_to_json, "w", encoding="utf-8") as f:
                f.write(json.dumps(tree, indent=4))
                print(f"New vault has been created: {vault_path_to_json}")
            
            copy_directory(Path(src_vault), Path(dst_folder))

        try:
            shutil.copytree(Path("assets"), dst_folder/"assets", ignore=shutil.ignore_patterns('script.js', 'style.css'))
        except:
            print("Assets folder already exists!")

        
        create_root(dst_folder, VAULTS_FOLDER/src_dir_name)
        create_js(dst_folder)
        create_menu(dst_folder)
        create_css(dst_folder)
        print(f"Vault has been converted to {dst_folder}")
    