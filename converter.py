import markdown
import sys
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
from os import path
import shutil
from pathlib import Path
from PIL import Image
from os import path
from html import escape

PATH_TO_IMAGES = "HTMLPages/images/"
ROOT_HTML = "index.html"

# def set_menu(links):
#     ul = '<ul class="menu">'
#     for li in links:
#         ul += f'<li>{li}</li>'
#     ul += '</ul>'
#     return ul


def set_menu(base_url: Path, root: Path):
    html = "<ul>\n"

    for item in sorted(root.iterdir()):
        if item.name.startswith('.') or item.name == "images" or item.name == "style.css":
            continue
        if item.name == ROOT_HTML:
            new_name = "HOME"
        else: new_name = item.stem
        # if item.suffix == ".md":
        #     # new_name = item.stem + ".html"
        #     # target_path = item.with_name(new_name)
        #     new_name = item.stem + ".html"
        # else:
        
        target_path = item.with_name(item.name)
        if not base_url.is_dir(): 
            base_url = base_url.parent
        relative_path = path.relpath(target_path, start=base_url)
        relative_path = relative_path.replace("\\", "/")
        
        # print("-"*10)
        
        # print(f"Root: {root}")
        # print(f"Target: {target_path}")
        # print(f"Relative: {relative_path}")
        # print("-"*10)
        if item.is_dir():
            html += f"<li><strong>{new_name}</strong>\n"
            html += set_menu(base_url, item)
            html += "</li>\n"
        else:
            html += f'<li><a href="{relative_path}">{new_name}</a></li>\n'

    html += "</ul>\n"
    return html


def create_menu(root):
    the_end = """
                    </div>
            </body>
        </html>
        """
    root_path = Path(root)
    for path in root_path.rglob("*"):
        if any(part.startswith('.') for part in path.parts):
            continue
        #print(path)
        if not path.is_dir():
            print(path.name)
            with open(path, "a", encoding="utf-8") as html:
                html.write(set_menu(path, root_path)+the_end)
                

def get_relative_path(src, dst):
    return path.relpath(dst, src)

def create_css(target):
    with open("style.css", "r") as css:
        css_text = css.read()
    with open(target+"style.css", "w") as f:
        f.write(css_text)

def create_root(root):
    with open("index.html", "r") as index:
        text = index.read()
    with open(root+"index.html", "w") as index:
        index.write(text)

def copy_directory(src, dst):

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

    src_path = Path(src)
    dst_path = Path(dst)

    for path in src_path.rglob("*"):
        CSS_PATH = Path("HTMLPages/style.css")
        if any(part.startswith('.') for part in path.parts):
            continue

        relative = path.relative_to(src_path)
        target = dst_path / relative
        #print(target)
        # shutil.copytree(
        #     src_path,
        #     dst_path,
        #     ignore=shutil.ignore_patterns(".*"),
        #     dirs_exist_ok=True  # дозволяє копіювати поверх існуючої структури (Python 3.8+)
        # )

        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)

        elif path.suffix == ".md":
            target = target.with_suffix(".html")
            target.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            blockquote = preprocess_callouts(text)
            photos = set_photos(blockquote, target)

            md_to_html = markdown.markdown(photos,extensions=["fenced_code"])

            #{set_menu(target, Path("HTMLPages"))}
            html_content = f"""
                <!DOCTYPE html>
                <html lang="uk">
                    <head>
                        <meta charset="UTF-8">
                        <title>Document</title>
                        <link rel="stylesheet" href={get_relative_path(target, CSS_PATH)}>
                    </head>
                    <body>
                        <h1>{target.stem}</h2>
                        <div class="main">
                            <div class="content">
                            {md_to_html}
                            </div>
                """

            with open(target, "w", encoding="utf-8") as f:
                f.write(html_content)
        elif path.suffix in image_extensions:
            img = Image.open(path)
            img.save(target)

def set_photos(html, current_path):
    # pattern = re.compile(
    #     r'!\[\[(.*?)\]\]', 
    #     flags=re.IGNORECASE)
    # if pattern.match(html):
    #     name_of_the_file = re.findall(pattern, html)[0]
    #     image_path = path.join(PATH_TO_IMAGES, name_of_the_file)
    #     def replacer(match):
    #         #filename = match.group(1).strip()
    #         return f'<img class="image" src="{image_path}">'
    #     try:
    #         #check if this is even file
    #         with open(image_path, 'r') as file:
    #             return pattern.sub(replacer, html)
    #     except:
    #         return
    # else:
    #     return
    pattern = re.compile(r'!\[\[(.+?)\]\]')

    def replacer(match):
        filename = match.group(1).strip()
        image_path = path.join(get_relative_path(path.dirname(current_path), PATH_TO_IMAGES), filename)
        return f'<div class="image-div"><img src="{image_path}" alt="{filename}" /></div>'

    return pattern.sub(replacer, html)

def preprocess_callouts(md_text):
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

# def convert_md_to_html(input_file, output_file):
#     pass
if __name__ == "__main__":
    # args = []
    # for arg in sys.argv[1:]:
    #     args.append(arg)
    copy_directory("D:\Web\Web", "HTMLPages")
    #convert_md_to_html(args[0], args[1])
    create_css("HTMLPages/")
    create_root("HTMLPages/")
    create_menu("HTMLPages")
    