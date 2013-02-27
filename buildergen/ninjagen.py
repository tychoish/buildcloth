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

from buildergen.buildfile import BuildFile
from buildergen.buildfile import BuildFileError

class NinjaFileError(BuildFileError):
    pass

class NinjaFileBuilder(BuildFile):
    def __init__(self, ninjafile=None):
        super(NinjaFileBuilder, self).__init__(ninjafile)
        self.ninja = self.buildfile

    # The following two methods allow more direct interaction with the
    # internal representation of the makefile than the other methods.

    def block(self, block):
        if block in self.builder:
            raise NinjaFileError('Cannot add "' + block + '" to ninja.build. ' + block + ' already exists.')
        else:
            self.builder[block] = []
            self.section_break(block, block)

    def raw(self, lines, block='_all'):
        if type(lines) is list:
            o = []
            for line in lines:
                if type(line) is list:
                    raise NinjaFileError('Cannot add nested lists to a Makefile with raw().')
                else:
                    o.append(line)
            self._add_to_builder(data=o, block=block, raw=True)
        else:
            raise NinjaFileError('Cannot add non-list raw() content to ninja.build.')

    # The following methods constitute the 'public' interface for
    # building makefile.

    def section_break(self, name, block='_all'):
        self._add_to_builder('\n\n########## ' + name + ' ##########', block)

    def comment(self, comment, block='_all'):
        self._add_to_builder('\n# ' + comment, block)

    def newline(self, n=1, block='_all'):
        for i in range(n):
            self._add_to_builder('', block)

    def var(self, variable, value, block='_all'):
        self._add_to_builder(variable + ' = ' + value, block)

    def rule(self, name, rule_dict, block='_all'):
        for i in rule_dict['command']:
            cmd += i + '; ' 

        if depfile in rule_dict:
            depf = rule_dict['depfile']
        else:
            depf = None
            
        if generator in rule_dict:
            gen = rule_dict['generator']
        else:
            gen = None
            
        if restat in rule_dict:
            rstat = rule_dict['restat']
        else:
            rstat = None
        
        if rspfile in rule_dict and rspfile_content in rule_dict:
            rsp = ( rule_dict['rspfile'], rule_dict['rspfile_content'] )
        else:
            rsp = None

        self._rule( name=name, 
                    command=cmd,
                    description=rule_dict['description'],
                    depfile=depf,
                    generator=gen, 
                    restat=rstat,
                    rsp=()
                    )

    def _rule(self, name, command, description, 
              depfile=None, generator=None, restat=False, rsp=None, block='_all'):
        o = [ 'rule ' + name ]
        o.append('  command = ' + command)
        o.append('  description = ' + name.upper() + ' ' + description)

        if depfile is not None:
            o.append('  depfile = ' + depfile)
        if generatior is not None:
            o.append('  generator = True')
        if restat is not False:
            o.append('  restat = True')
        if rsp is not None:
            o.append('  rspfile = ' + rsp[0])
            o.append('  rspfile_content = ' + rsp[1])

        self._add_to_builder(data=o, block=block, raw=True)

    def build(self, path, rule, dep=[], vars={}, 
              order_only=[], implicit=[], block='_all'):

        o = [ 'build %s: %s' % ( path, rule ) ]
        for d in dep:
            o[0] += d + ' '

        if implicit:
            o[0] += ' |'
            for dep in implicit:
                o[0] += ' ' + dep

        if order_only:
            o[0] += ' |'
            for dep in order_only:
                o[0] += ' ' + dep

        if vars: 
            for var in items(vars):
                o.append('  %s = %s' % ( var[0], var[1] ) )

        self.add_to_builder(data=o, block=block, raw=True)

    def default(self, rule, block='_all'):
        self.add_to_builder('default ' + rule, block)
