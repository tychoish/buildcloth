#!/usr/bin/python

import argparse

def content():
    o = ['#!/usr/bin/python\n']

    with open('buildergen/makefilegen.py', 'r') as f:
        for lines in f.readlines()[:14]:
            o.append(lines.rstrip())
    
    o.append('\n')

    with open('buildergen/buildfile.py', 'r') as f: 
        o.append(f.read())

    with open('buildergen/makefilegen.py', 'r') as f:
        for lines in f.readlines()[16:]:
            o.append(lines.rstrip())
        
    return o

def main():
    parser = argparse.ArgumentParser("Building a copy of the Makefile Generator for embedding in other modules.")
    parser.add_argument('filename', help='name of the filename to write to.', default='makefile_builder.py', nargs=1)
    args = parser.parse_args()

    with open(args.filename[0], 'w') as f: 
        for line in content():
            f.write(line + '\n')

if __name__ == '__main__':
    main()
