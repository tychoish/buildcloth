import json

def dump_args_to_json_file(a=None, b=None, fn='t'):
    with open(fn, 'a') as f:
        json.dump((a,b), f)

def dump_args_to_json_file_with_newlines(a=None, b=None, fn='t'):
    with open(fn, 'a') as f:
        json.dump((a,b), f)
        f.write('\n')

def dummy_function(a=None, b=None):
    return a, b
