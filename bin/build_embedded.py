#!/usr/bin/python

import argparse

def content(input):
    o = ['#!/usr/bin/python\n']

    with open('buildergen/buildfile.py', 'r') as f: 
        o.append(f.read())

    with open(input, 'r') as f:
        for lines in f.readlines()[18:]:
            o.append(lines.rstrip())
        
    return o

def main():
    parser = argparse.ArgumentParser("Building a copy of the Makefile Generator for embedding in other modules.")
    parser.add_argument('filename', help='name of the filename to write to.', default='makefile_builder.py', nargs=1)
    parser.add_argument('input', help='name of the builder source.', default='', nargs=1)

    args = parser.parse_args()

    with open(args.filename[0], 'w') as f: 
        for line in content(args.input[0]):
            f.write(line + '\n')

if __name__ == '__main__':
    main()
