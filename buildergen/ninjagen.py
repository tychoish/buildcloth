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
    def __init__(self, ninjafile=None, indent=2):
        super(NinjaFileBuilder, self).__init__(ninjafile)
        self.ninja = self.buildfile
        self.indent = ' ' * indent 

    # The following methods constitute the 'public' interface for
    # building makefile.

    def rule(self, name, rule_dict, block='_all'):
        if type(rule_dict['command']) is str:
            raise BuildFileError('ERROR: ' + rule_dict['command'] + ' is not a list.')
        elif len(rule_dict['command']) == 1:
            cmd = rule_dict['command'][0]
        else:     
            cmd = ''
            for i in rule_dict['command']:
                cmd += i + '; ' 

        if 'depfile' in rule_dict:
            depf = rule_dict['depfile']
        else:
            depf = None
            
        if 'generator' in rule_dict:
            gen = rule_dict['generator']
        else:
            gen = None
            
        if 'restat' in rule_dict:
            rstat = rule_dict['restat']
        else:
            rstat = False
        
        if 'rspfile' in rule_dict and 'rspfile_content' in rule_dict:
            rsp = ( rule_dict['rspfile'], rule_dict['rspfile_content'] )
        else:
            rsp = None

        self.add_rule( name=name, 
                       command=cmd,
                       description=rule_dict['description'],
                       depfile=depf,
                       generator=gen, 
                       restat=rstat,
                       rsp=rsp,
                       block=block
                     )

    def add_rule(self, name, command, description, 
              depfile=None, generator=None, restat=False, rsp=None, block='_all'):
        o = [ 'rule ' + name ]
        o.append(self.indent + 'command = ' + command)
        o.append(self.indent + 'description = ' + name.upper() + ' ' + description)

        if depfile is not None:
            o.append(self.indent + 'depfile = ' + depfile)
        if generator is not None:
            o.append(self.indent + 'generator = True')
        if restat is not False:
            o.append(self.indent + 'restat = True')
        if rsp is not None:
            o.append(self.indent + 'rspfile = ' + rsp[0])
            o.append(self.indent + 'rspfile_content = ' + rsp[1])

        self._add_to_builder(data=o, block=block, raw=True)

    def build(self, path, rule, dep=[], vars={}, 
              order_only=[], implicit=[], block='_all'):

        o = [ 'build %s: %s' % ( path, rule ) ]
        for d in dep:
            o[0] += ' ' + d

        if implicit:
            o[0] += ' |'
            for dep in implicit:
                o[0] += ' ' + dep

        if order_only:
            o[0] += ' ||'
            for dep in order_only:
                o[0] += ' ' + dep

        if vars: 
            for var in vars.items():
                o.append('%s%s = %s' % ( self.indent, var[0], var[1] ) )

        self._add_to_builder(data=o, block=block, raw=True)

    def default(self, rule, block='_all'):
        self._add_to_builder('default ' + rule, block)
