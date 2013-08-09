import json

def dump_args_to_json_file(a=None, b=None):
    with open('t', 'a') as f:
        json.dump((a,b), f)

def dummy_function(a=None, b=None):
    return a, b
