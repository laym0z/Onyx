import markdown
import re
from os import path, remove
from pathlib import Path
from PIL import Image
import shutil
import hashlib
import json
import modules.config as config


class Converter():
    
    def __init__(self, config_storage):
        self.config_storage = config_storage
        self.folder_id_counter = 0

    def create_css(self, dst: Path):
        with open(Path(self.config_storage['ROOT_CSS']), "r") as css:
            css_text = css.read()
        with open(dst / Path(self.config_storage['ROOT_CSS']), "w") as f:
            f.write(css_text)

    def create_root(self, dst: Path, vault_folder: Path):
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
                <link rel="stylesheet" href="{Path(self.config_storage['ROOT_CSS'])}">
                <link rel="icon" href="{Path(self.config_storage['PATH_TO_FAVICON'])}" type="image/x-icon">
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
            <script src="{Path(self.config_storage['ROOT_JS'])}"></script>
            </html>
        """
        with open(dst / Path(self.config_storage['ROOT_HTML']), "w", encoding="utf-8") as index:
            index.write(html_content)

    def create_js(self, dst: Path):
        with open(Path(self.config_storage['ROOT_JS']), "r") as index:
            text = index.read()
        with open(dst / Path(self.config_storage['ROOT_JS']), "w") as index:
            index.write(text)   

    #-----------------------JSON VAULT------------------------------

    def generate_json(self, src_vault: Path) -> dict:
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
                node[name] = self.file_hash(sub_path)
        return tree

    def flatten(self, tree, prefix=""):
        files = {}
        dirs = []
        for name, value in tree.items():
            current_path = f"{prefix}/{name}" if prefix else name

            if isinstance(value, dict):
                # This is dir
                dirs.append(current_path)

                sub_files, sub_dirs = self.flatten(value, current_path)
                files.update(sub_files)
                dirs.extend(sub_dirs)
            else:
                # This is file
                files[current_path] = value

        return files, dirs

    #----------------------FILES AND DIRS---------------------------

    def file_hash(self, path: Path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def delete_dirs_and_files(self, remove_files: dict, remove_dirs: dict, dst: Path):
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
    def set_menu(self, sub_path: Path, dst_path: Path, dst_folder: Path) -> str:
        home_page = ""
        html = "<ul class='sub-list'>\n"

        for item in sorted(dst_path.iterdir()):
            if item.name.startswith('.') or item.name in self.config_storage['blacklist_files']:
                continue
            if item.name == self.config_storage['ROOT_HTML']:
                new_name = "HOME"
            else: new_name = item.stem
            
            target_path = item.with_name(item.name)
            if not sub_path.is_dir(): 
                sub_path = sub_path.parent
            relative_path = path.relpath(target_path, start=sub_path)
            relative_path = relative_path.replace("\\", "/")

            
            assets_path = path.relpath(dst_folder/Path(self.config_storage['PATH_TO_FOLDER_ICON']), start=sub_path)

            if item.is_dir():
                self.folder_id_counter+=1
                html += f"<li class='folder' data-folderID='{self.folder_id_counter}'><strong class='folder-name'><img src='{assets_path}'>{new_name}</strong>\n"
                html += self.set_menu(sub_path=sub_path, dst_path=item, dst_folder=dst_folder)
                html += "</li>\n"
            else:
                if item.name == self.config_storage['ROOT_HTML']:
                    home_page = f'<h1 class="home"><a href="{relative_path}">{new_name}</a></h1>\n'
                else:
                    html += f'<li class="file"><a href="{relative_path}">{new_name}</a></li>\n'

        html += "</ul>\n"
        return home_page+html

    def create_menu(self, dst_path: Path):
        for sub_path in dst_path.rglob("*"):
            if any(part.startswith('.') for part in sub_path.parts):
                continue
            if not sub_path.is_dir():
                # print(path.name)
                if sub_path.suffix == ".html":
                    with open(sub_path, "r", encoding="utf-8") as html:
                        data = html.read()
                    with open(sub_path, "w", encoding="utf-8") as html:
                        data = data.replace(self.config_storage['MENU_PLACEHOLDER_NAME'], f"<div class='menu'>{self.set_menu(sub_path=sub_path, dst_path=dst_path, dst_folder=dst_path)}</div>")
                        self.folder_id_counter = 0
                        html.write(data)            
    
    #---------------------------CONVERT------------------------------------

    def make_changes(self, tree: dict, vault_path: Path, src_vault: Path, dst_path: Path):
        with open(vault_path, "r", encoding="utf-8") as f:
            old_json = json.load(f)

            new_files, new_dirs = self.flatten(tree[src_vault.name])
            old_files, old_dirs = self.flatten(old_json[src_vault.name])
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
                self.delete_dirs_and_files(removed_files, removed_dirs, dst_path)
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
            print(f"Changes has been stored: {vault_path}")

    def write_changes_to_json(self, tree: dict, vault_path_to_json: Path):
        with open(vault_path_to_json, "w", encoding="utf-8") as f:
                f.write(json.dumps(tree, indent=4))

    def copy_directory(self, src_path: Path, dst_path: Path):
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

                blockquote = self.note_blocks(text)
                photos = self.set_photos(blockquote, target, dst_path)

                md_to_html = markdown.markdown(photos,extensions=["fenced_code", "extra"])
                html_content = f"""
                    <!DOCTYPE html>
                    <html lang="uk">
                        <head>
                            <meta charset="UTF-8">
                            <title>{target.stem}</title>
                            <link rel="stylesheet" href={path.relpath(dst_path / Path(self.config_storage['ROOT_CSS']), target.parent)}>
                            <link rel="icon" href={path.relpath(dst_path/Path(self.config_storage['PATH_TO_FAVICON']), target.parent)} type="image/x-icon">
                        </head>
                        <body>
                            
                            <div class="main">
                                {self.config_storage['MENU_PLACEHOLDER_NAME']}
                                <div class="content">
                                <h1 class="topic-name">{target.stem}</h2>
                                {md_to_html}
                                </div>
                            </div>
                        </body>
                        <footer>
                            <p>Created with <a href="https://github.com/laym0z/Onyx">Onyx</a> by <a href=https://github.com/laym0z>laym0z</a></p>
                        </footer>
                        <script src={path.relpath(dst_path / Path(self.config_storage['ROOT_JS']), target.parent)}></script>
                    </html>
                    """
                # print(target.name)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(html_content)

            elif sub_path.suffix in image_extensions:
                img = Image.open(sub_path)
                img.save(target)

    #---------------------------STYLING------------------------------------

    def set_photos(self, html: str, current_path: Path, dst_path: Path) -> str:
        pattern = re.compile(r'!\[\[(.+?)\]\]')

        def replacer(match):
            filename = match.group(1).strip()
            image_path = path.join(path.relpath(dst_path / Path(self.config_storage['PATH_TO_IMAGES']), current_path.parent), filename)
            
            return f'<div class="image-div"><img src="{image_path}" alt="{filename}" /></div>'

        return pattern.sub(replacer, html)

    def note_blocks(self, md_text: str) -> str:
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
