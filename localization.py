import json
import os

res_dir_name = "resources/"
json_suffix = ".json"

def load_files():
    files_list = os.listdir(res_dir_name)
    json_files = [
        file_name
        for file_name in files_list
        if file_name.endswith(json_suffix)]
    locales = dict()
    for json_file_name in json_files:
        file_path = res_dir_name + json_file_name
        locales_dict_key = json_file_name[:-5]
        with open(file_path, "r") as file:
            data = file.read()
            locale_dict = json.loads(data)
            locales[locales_dict_key] = locale_dict
    print(locales)
    return locales
