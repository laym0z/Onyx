import markdown
import re
from os import path, remove, rmdir
from pathlib import Path
from PIL import Image
import sys
import shutil
from tabulate import tabulate
import hashlib
import json

#TODO: REWRITE THIS WHOLE SHITCODE, HOLY FUCK

DEFAULT_JSON_FOLDER = Path("Vaults")
DEFAULT_DST_FOLDER = Path("HTMLPages")
PATH_TO_IMAGES = Path("images/")
PATH_TO_FOLDER_ICON = Path("assets/icons/folder.png")
PATH_TO_FAVICON = Path("assets/icons/favicon.ico")
ROOT_MD = "index.md"
ROOT_HTML = "index.html"
ROOT_CSS = Path("assets/style.css")
ROOT_JS = Path("assets/script.js")
DST_CSS = Path("style.css")
DST_HTML = Path("index.html")
DST_JS = Path("script.js")



MENU_PLACEHOLDER_NAME = "<div class='PLACEHODER'></div>"

ARGS = {
    "--help": "print help menu",
    "--src": "source directory (--src [PATH])",
    "--dst": "destination directory (--dst [PATH])",
    "--ri": "write or rewrite main page",
    "--rc": "write or rewrite style.css "
}
blacklist_menu = ["images", "style.css", "assets", "script.js"]


def file_hash(path: Path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def flatten(tree, prefix=""):
    result = {}
    dirs = []
    # for name, value in tree.items():
    #     path = f"{prefix}/{name}" if prefix else name

    #     if isinstance(value, dict):
    #         result.update(flatten(value, path))
    #     else:
    #         result[path] = value

    # return result
    for name, value in tree.items():
        current_path = f"{prefix}/{name}" if prefix else name

        if isinstance(value, dict):
            # це директорія
            dirs.append(current_path)

            sub_files, sub_dirs = flatten(value, current_path)
            result.update(sub_files)
            dirs.extend(sub_dirs)
        else:
            # це файл
            result[current_path] = value

    return result, dirs

def set_menu(sub_path: Path, dst_path: Path, folder_id_counter: int) -> str:
    home_page = ""
    html = "<ul class='sub-list'>\n"

    for item in sorted(dst_path.iterdir()):
        if item.name.startswith('.') or item.name in blacklist_menu:
            continue
        if item.name == ROOT_HTML:
            new_name = "HOME"
        else: new_name = item.stem
        
        target_path = item.with_name(item.name)
        if not sub_path.is_dir(): 
            sub_path = sub_path.parent
        relative_path = path.relpath(target_path, start=sub_path)
        relative_path = relative_path.replace("\\", "/")

        folder_id_counter+=1

        assets_path = path.relpath(DEFAULT_DST_FOLDER/PATH_TO_FOLDER_ICON, start=sub_path)

        if item.is_dir():
            html += f"<li class='folder' data-folderID='{folder_id_counter}'><strong class='folder-name'><img src='{assets_path}'>{new_name}</strong>\n"
            html += set_menu(sub_path, item, folder_id_counter)
            html += "</li>\n"
        else:
            if item.name == ROOT_HTML:
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
                    data = data.replace(MENU_PLACEHOLDER_NAME, f"<div class='menu'>{set_menu(sub_path, dst_path, folder_id_counter)}</div>")
                    # html.write(set_menu(path, root_path))
                    html.write(data)
                
def get_relative_path(src: Path, dst: Path):
    return path.relpath(dst, src)

def create_css(dst: Path):
    with open(ROOT_CSS, "r") as css:
        css_text = css.read()
    with open(dst / DST_CSS, "w") as f:
        f.write(css_text)

def create_root(dst: Path):
    try:
        with open(ROOT_MD, "r", encoding="utf-8") as index:
            text = index.read()
            md_to_html = markdown.markdown(text,extensions=["fenced_code"])
    except:
        md_to_html="<h1>Main Page</h1>"
    html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Main Page</title>
            <link rel="stylesheet" href="style.css">
            <link rel="icon" href="assets/icons/favicon.ico" type="image/x-icon">
        </head>
        <body>
            
            <div class="main">
                <div class='PLACEHODER'></div>
                <div class="content">
                    {md_to_html}
                </div>
            </div>
            
        </body>
        <script src="{DST_JS}"></script>
        </html>
    """
    with open(dst / DST_HTML, "w", encoding="utf-8") as index:
        index.write(html_content)

def create_js(dst: Path):
    with open(ROOT_JS, "r") as index:
        text = index.read()
    with open(dst / DST_JS, "w") as index:
        index.write(text)    


def delete_dirs_and_files(remove_list: dict, removed_dirs: dict, dst: Path):
    for value in remove_list:
        new_name = path.splitext(value)[0]+'.html'
        # file_name = path.basename(new_name)
        new_path = Path(dst/new_name)
        if not new_path.is_dir():
            remove(new_path)
        else:
            pass
    for value in removed_dirs:
        path_obj = Path(value)
        dir_name = path.basename(path_obj)
        new_path = Path(dst/dir_name)
        try:
            shutil.rmtree(new_path, ignore_errors=True)
        except:
            continue

#TODO: THIS FUNCTION NO LONGER REQUIRES THE CREATION OF A NEW DIRECTORY TREE, THIS FUNCTIONALITY SHOULD BE MOVED TO THE FUNCTION
def copy_directory(src_path: Path, dst_path: Path):
    tree = {src_path.name: {}}
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

        node = tree[src_path.name]
        parts = relative.parts

        for part in parts[:-1]:
            node = node.setdefault(part, {})

        name = parts[-1]
        
        if sub_path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            node.setdefault(name, {})

        elif sub_path.suffix == ".md":
            node[name] = file_hash(sub_path)
            target = target.with_suffix(".html")
            target.parent.mkdir(parents=True, exist_ok=True)

            with open(sub_path, "r", encoding="utf-8") as f:
                text = f.read()

            blockquote = preprocess_callouts(text)
            photos = set_photos(blockquote, target, dst_path)

            md_to_html = markdown.markdown(photos,extensions=["fenced_code", "extra"])

            html_content = f"""
                <!DOCTYPE html>
                <html lang="uk">
                    <head>
                        <meta charset="UTF-8">
                        <title>{target.stem}</title>
                        <link rel="stylesheet" href={get_relative_path(target.parent, dst_path / DST_CSS)}>
                        <link rel="icon" href={get_relative_path(target.parent, DEFAULT_DST_FOLDER/PATH_TO_FAVICON)} type="image/x-icon">
                    </head>
                    <body>
                        
                        <div class="main">
                            {MENU_PLACEHOLDER_NAME}
                            <div class="content">
                            <h1 class="topic-name">{target.stem}</h2>
                            {md_to_html}
                            </div>
                        </div>
                    </body>
                    <script src={get_relative_path(target.parent, dst_path / DST_JS)}></script>
                </html>
                """
            if not target.exists():
                # print(target.name)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(html_content)
        elif sub_path.suffix in image_extensions:
            img = Image.open(sub_path)
            img.save(target)
    if not DEFAULT_JSON_FOLDER.is_dir():
        DEFAULT_JSON_FOLDER.mkdir(parents=True, exist_ok=True)
    with open(DEFAULT_JSON_FOLDER/"vaults.json", "w", encoding="utf-8") as json_file:
        json_file.write(json.dumps(tree, indent=4))


def set_photos(html: str, current_path: Path, dst_path: Path) -> str:
    pattern = re.compile(r'!\[\[(.+?)\]\]')

    def replacer(match):
        filename = match.group(1).strip()
        image_path = path.join(get_relative_path(current_path.parent, dst_path / PATH_TO_IMAGES), filename)
        
        return f'<div class="image-div"><img src="{image_path}" alt="{filename}" /></div>'

    return pattern.sub(replacer, html)

def preprocess_callouts(md_text: str) -> str:
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
    CREATE_HTML = False
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
                    DEFAULT_DST_FOLDER = Path(arguments[i+1])
                except:
                    print(f"Path is invalid: {src_vault}")
                    print_help()
                    sys.exit()
            elif arg == "--ri":
                CREATE_HTML=True
            elif arg == "--rc":
                CREATE_CSS=True
            
            i+=1
        #TODO: THIS NEEDS TO BE MOVED TO A FUNCTION
        if path.isdir(DEFAULT_DST_FOLDER):

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
            
            new_json = json.dumps(tree, indent=4)

            dir_name = path.basename(src_vault)

            vault_path = DEFAULT_JSON_FOLDER/f"{dir_name}.json"
            print(vault_path)
            if path.exists(vault_path):
                with open(vault_path, "r", encoding="utf-8") as f:
                    old_json = json.load(f)
                    #old_json = {src_vault.name: old_json.get(src_vault.name)}
                # print(f"Old JSON: {old_json}, Type: {type(old_json)}")
                # print(f"New JSON: {new_json}, Type: {type(new_json)}")
                # print(DeepDiff(old_json, new_json, ignore_order=True))

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
                    delete_dirs_and_files(removed_files, removed_dirs, DEFAULT_DST_FOLDER)
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
                    copy_directory(Path(src_vault), Path(DEFAULT_DST_FOLDER))
            else:
                with open(vault_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(tree, indent=4))
        else:
            print("There is nothing to convert")
        if CREATE_CSS:
            create_css(DEFAULT_DST_FOLDER)
        if CREATE_HTML:
            create_root(DEFAULT_DST_FOLDER)
        try:
            shutil.copytree(Path("assets"), DEFAULT_DST_FOLDER/"assets", ignore=shutil.ignore_patterns('script.js', 'style.css'))
        except:
            print("Assets folder already exists!")
        create_js(DEFAULT_DST_FOLDER)
        create_menu(DEFAULT_DST_FOLDER)
        
        print(f"Vault was converted to {DEFAULT_DST_FOLDER}")
    