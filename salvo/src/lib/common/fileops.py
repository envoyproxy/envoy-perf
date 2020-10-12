import json
import random
import yaml
import glob
import os
import tempfile

def open_json(path, mode='r'):
    """
    Open a json file and return its contents as a dictionary
    """
    data = None
    with open(path, mode) as json_file:
        data = json.loads(json_file.read())
    return data

def open_yaml(path, mode='r'):
    """
    Open a yaml file and return its contents as a dictionary
    """
    data = None
    with open(path, mode) as yaml_file:
        data = yaml.load(yaml_file)
    return data

def delete_directory(path):
    """
    Nuke a directory and its contents
    """
    for found_file in glob.glob(os.path.join(path, '*')):
        os.unlink(found_file)
    os.rmdir(path)

#  vim: set ts=4 sw=4 tw=0 et :
