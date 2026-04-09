from os import path, mkdir
from pathlib import Path
import sys
import shutil
from tabulate import tabulate
import json
import modules.config as config
from modules.Converter import Converter


#TODO: REWRITE THIS WHOLE SHITCODE, HOLY FUCK

#TODO: TRACK ASSETS FOLDER CHANGES

def copy_assets():
    try:
        shutil.copytree(Path("assets"), dst_folder/"assets", ignore=shutil.ignore_patterns('script.js', 'style.css'))
    except:
        print("Assets folder already exists!")

#-------------------HELP---------------

ARGS = {
    "--help": "print help menu",
    "--src": "source directory (--src [PATH])",
    "--dst": "destination directory (--dst [PATH])",
    "--rc": "write or rewrite style.css "
}

def print_help():
    list = []
    for key, value in ARGS.items():
        list.append([key, value])
    print(tabulate(list))

#------------------MAIN----------------

if __name__ == "__main__":
    CREATE_CSS = False
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
            elif arg == "--rc":
                CREATE_CSS=True
            
            i+=1

        #-------------CONFIG----------------------

        vault = config.get_vault()
        src_dir_name = path.basename(src_vault)
        if not path.exists(vault/src_dir_name/config.get_config_file()):
            config.create_config(Path(vault/src_dir_name))
            print("Config file has been created!")
        config_storage = config.read_config(Path(src_dir_name))
        #------------------------------------------

        converter = Converter(config_storage)
        
        if CREATE_CSS:
            converter.create_css(dst_folder)
            print("Style has been updated!")
            sys.exit()

        #---------------------GENERATE NEW JSON------------------------- 
        tree = converter.generate_json(src_vault)
        new_json = json.dumps(tree, indent=4)

        vault_path_to_json = vault/src_dir_name/f"{src_dir_name}.json"

        #---------------------WRITE CHANGES AND COPY DIRECTORY IF JSON FILE EXISTS----------------
        if path.exists(vault_path_to_json):

            #-----------------------DELETE FOLDERS OF FILES THAT HAVE BEEN DELETED IN THE SOURCE VAULT-----------
            converter.make_changes(tree, vault_path_to_json, src_vault, dst_folder)
            #-----------------------------------------------------------------------------------------------------
            
            converter.write_changes_to_json(tree, vault_path_to_json)
        #--------------------CREATE VAULT FOLDER AND COPY DIRECTORY IF IT DOES NOT EXIST---------------
        else:
            if not path.exists(vault/src_dir_name):
                mkdir(vault/src_dir_name)
            converter.write_changes_to_json(tree, vault_path_to_json)
            print(f"New vault has been created: {vault_path_to_json}")
            
        converter.copy_directory(Path(src_vault), Path(dst_folder))
        copy_assets()
        converter.create_root(dst_folder, vault/src_dir_name)
        converter.create_js(dst_folder)
        converter.create_menu(dst_folder)
        converter.create_css(dst_folder)
        print(f"Vault has been converted to {dst_folder}")
    