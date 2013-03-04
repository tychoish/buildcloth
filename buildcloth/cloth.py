# Copyright 2012 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Sam Kleinman (tychoish)

import os.path
import os

def print_output(list):
    for line in list:
        print(line)

def write_file(list, filename):
    dirpath = filename.rsplit('/', 1)[0]
    if os.path.isdir(dirpath) is False:
        os.mkdir(dirpath)

    with open(filename, 'w') as f:
        for line in list:
            f.write(line + '\n')

class BuildClothError(Exception):
    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        if self.msg is None:
            return "Error in consstructing BuildCloth."
        else:
            return "Error: " + self.msg

class BuildCloth(object):
    def __init__(self, buildfile=None):
        self.builder = { '_all' : [] }
        self.buildfile = self.builder['_all']

        if buildfile is None:
            pass
        elif type(buildfile) is list:
            for line in buildfile:
                if type(line) is list:
                    raise BuildClothError('Cannot instantiate BuildCloth with nested list.')
                    break
                else:
                    self.builder['_all'].append(line)
        else:
            raise BuildClothError('Instantiated BuildCloth object with malformed argument.')

    # The following two methods allow more direct interaction with the
    # internal representation of the buildfile.

    def block(self, block):
        if block in self.builder:
            raise NinjaFileError('Cannot add "%s" to ninja.build. %s already exists.' 
                                 % (block, block))
        else:
            self.builder[block] = []
            self.section_break(block, block)

    def raw(self, lines, block='_all'):
        if type(lines) is list:
            o = []
            for line in lines:
                if type(line) is list:
                    raise BuildClothError('Cannot add nested lists with raw().')
                else:
                    o.append(line)
            self._add_to_builder(data=o, block=block, raw=True)
        else:
            raise BuildClothError('Cannot add non-list raw() content.')

    # Basic commenting and other formatting niceties that are not builder
    # specific but are generally userfacing.

    def section_break(self, name, block='_all'):
        self._add_to_builder('\n\n########## ' + name + ' ##########', block)

    def comment(self, comment, block='_all'):
        self._add_to_builder('\n# ' + comment, block)

    def newline(self, n=1, block='_all'):
        for i in range(n):
            self._add_to_builder('', block)

    def var(self, variable, value, block='_all'):
        self._add_to_builder(variable + ' = ' + value, block)

    # the following method is used internally to constrcd uct and
    # maintain the internal representation of the buildfile.

    def _add_to_builder(self, data, block, raw=False):
        def add(data, block):
            if block is '_all':
                pass
            else:
                self.buildfile.append(data)

            if block in self.builder:
                self.builder[block].append(data)
            else:
                self.builder[block] = [data]

        if raw is True:
            for line in data:
                add(line, block)
        elif type(data) is not str or raw is True:
            raise BuildClothError('Added malformed data to BuildCloth.')
        else:
            add(data, block)

    # The following methods produce output for public use.

    def get_block(self, block='_all'):
        return self.builder[block]

    def print_content(self, block_order=['_all']):
        output = []

        if type(block_order) is not list:
            raise BuildClothError('Cannot print blocks not specified as a list.')
        else:
            for block in block_order:
                output.append(self.builder[block])

            output = [item for sublist in output for item in sublist]
            print_output(output)

    def print_block(self, block='_all'):
        if block not in self.builder:
            raise BuildClothError('Error: ' + block + ' not specified in buildfile')
        else:
            print_output(self.builder[block])

    def write(self, filename, block_order=['_all']):
        output = []

        if type(block_order) is not list:
            raise BuildClothError('Cannot write blocks not specified as a list.')
        else:
            for block in block_order:
                output.append(self.builder[block])

            output = [item for sublist in output for item in sublist]
            write_file(output, filename)

    def write_block(self, filename, block='_all'):
        if block not in self.builder:
            raise BuildClothError('Error: ' + block + ' not specified in buildfile')
        else:
            write_file(self.builder[block], filename)
