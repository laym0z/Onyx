import markdown
import re
from os import path
from pathlib import Path
from PIL import Image
import sys

DEFAULT_DST_FOLDER = Path("HTMLPages")
PATH_TO_IMAGES = Path("images/")
ROOT_HTML = "index.html"
ROOT_CSS = "style.css"
MENU_PLACEHOLDER_NAME = "<div class='PLACEHODER'></div>"

ARGS = {
    "help": "--help",
    "src": "--src",
    "dst": "--dst",
    "overwrite": "--overwrite",
    "root-index": "--ri",
    "root-css": "--rc"
}

def set_menu(base_url: Path, root: Path) -> str:
    html = "<ul>\n"

    for item in sorted(root.iterdir()):
        if item.name.startswith('.') or item.name == "images" or item.name == "style.css":
            continue
        if item.name == ROOT_HTML:
            new_name = "HOME"
        else: new_name = item.stem
        
        target_path = item.with_name(item.name)
        if not base_url.is_dir(): 
            base_url = base_url.parent
        relative_path = path.relpath(target_path, start=base_url)
        relative_path = relative_path.replace("\\", "/")
        if item.is_dir():
            html += f"<li><strong>{new_name}</strong>\n"
            html += set_menu(base_url, item)
            html += "</li>\n"
        else:
            html += f'<li><a href="{relative_path}">{new_name}</a></li>\n'

    html += "</ul>\n"
    return html

def create_menu(root_path: Path):
    for path in root_path.rglob("*"):
        if any(part.startswith('.') for part in path.parts):
            continue
        if not path.is_dir():
            # print(path.name)
            if path.suffix == ".html":
                with open(path, "r", encoding="utf-8") as html:
                    data = html.read()
                with open(path, "w", encoding="utf-8") as html:
                    data = data.replace(MENU_PLACEHOLDER_NAME, set_menu(path, root_path))
                    # html.write(set_menu(path, root_path))
                    html.write(data)
                
def get_relative_path(src: Path, dst: Path):
    return path.relpath(dst, src)

def create_css(dst: Path):
    with open(ROOT_CSS, "r") as css:
        css_text = css.read()
    with open(dst / ROOT_CSS, "w") as f:
        f.write(css_text)

def create_root(dst: Path):
    with open(ROOT_HTML, "r") as index:
        text = index.read()
    with open(dst / ROOT_HTML, "w") as index:
        index.write(text)

def copy_directory(src_path: Path, dst_path: Path, OVERWRITE: bool):

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

    for path in src_path.rglob("*"):
        if any(part.startswith('.') for part in path.parts):
            continue

        relative = path.relative_to(src_path)
        target = dst_path / relative

        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)

        elif path.suffix == ".md":
            target = target.with_suffix(".html")
            target.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            blockquote = preprocess_callouts(text)
            photos = set_photos(blockquote, target, dst_path)

            md_to_html = markdown.markdown(photos,extensions=["fenced_code"])

            #{set_menu(target, Path("HTMLPages"))}
            html_content = f"""
                <!DOCTYPE html>
                <html lang="uk">
                    <head>
                        <meta charset="UTF-8">
                        <title>{target.stem}</title>
                        <link rel="stylesheet" href={get_relative_path(target.parent, dst_path / ROOT_CSS)}>
                    </head>
                    <body>
                        <h1 class="topic-name">{target.stem}</h2>
                        <div class="main">
                            {MENU_PLACEHOLDER_NAME}
                            <div class="content">
                            {md_to_html}
                            </div>
                        </div>
                    </body>
                </html>
                """
            if not target.exists() or (target.exists() and OVERWRITE):
                print(target.name)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(html_content)
        elif path.suffix in image_extensions:
            img = Image.open(path)
            img.save(target)

def set_photos(html: str, current_path: Path, dst_path: Path) -> str:
    pattern = re.compile(r'!\[\[(.+?)\]\]')

    def replacer(match):
        filename = match.group(1).strip()
        image_path = path.join(get_relative_path(current_path.parent, dst_path / PATH_TO_IMAGES), filename)
        
        return f'<div class="image-div"><img src="{image_path}" alt="{filename}" /></div>'

    return pattern.sub(replacer, html)

def preprocess_callouts(md_text: str) -> str:
    """
    Замінює Obsidian-style callouts на HTML <div> перед Markdown конвертацією.
    Підтримує: note, warning, tip, info
    """
    # regex шукає блок > [!type] або просто [!type]
    pattern = re.compile(
        r'(?:^>?\s*)\[!(note|warning|tip|info)\]\s*(.*)', 
        flags=re.IGNORECASE
    )

    def replacer(match):
        callout_type = match.group(1).lower()
        content = match.group(2).strip()
        return f'<div class="callout callout-{callout_type}">{content}</div>'

    # Застосовуємо заміну рядок за рядком
    processed_lines = []
    for line in md_text.split("\n"):
        processed_lines.append(pattern.sub(replacer, line))

    return "\n".join(processed_lines)

#-------------------HELP---------------

def print_help():
    print(ARGS)

#------------------MAIN----------------

if __name__ == "__main__":
    CREATE_CSS = False
    CREATE_HTML = False
    OVERWRITE = False
    arguments = []
    for arg in sys.argv[1:]:
        arguments.append(arg)
    if len(arguments) == 0 or (len(arguments) == 1 and arguments[0] != "--help"):
        print_help()
    elif not ARGS["src"] in arguments: 
        print("Please, provide the obssdian vault with '--src VAULT'")
    else:
        i = 0
        for arg in arguments:
            if arg == ARGS["help"]: 
                print_help()
                sys.exit()
            elif arg == ARGS["src"]:
                try:
                    src_vault = Path(arguments[i+1])
                    if not src_vault.exists():
                        print(f"Provided source path does not exist: {src_vault}")
                        sys.exit()
                except:
                    print_help()
                    sys.exit()
            elif arg == ARGS["dst"]:
                try:
                    DEFAULT_DST_FOLDER = Path(arguments[i+1])
                except:
                    print(f"Path is invalid: {src_vault}")
                    print_help()
                    sys.exit()
            elif arg == ARGS["root-index"]:
                CREATE_HTML=True
            elif arg == ARGS["root-css"]:
                CREATE_CSS=True
            elif arg == ARGS["overwrite"]:
                OVERWRITE=True
            
            i+=1
        
        copy_directory(Path(src_vault), Path(DEFAULT_DST_FOLDER), OVERWRITE)
        if CREATE_CSS:
            create_css(DEFAULT_DST_FOLDER)
        if CREATE_HTML:
            create_root(DEFAULT_DST_FOLDER)
        create_menu(Path(DEFAULT_DST_FOLDER))
        print(f"Vault was converted to {DEFAULT_DST_FOLDER}")
    