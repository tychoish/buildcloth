# Copyright 2013, Sam Kleinman
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

from buildcloth.makefile import MakefileCloth
from buildcloth.ninja import NinjaFileCloth

class Rule(object):
    def __init__(self, name=None):
        self._rule = { 'name': name }

    def name(self, name=None):
        if name is None and self._rule['name'] is None:
            raise Exception('Rules must have names.')
        elif name is None:
            return self._rule['name']
        else: 
            self._rule['name'] = name
            return True

    def command(self, cmd=None):
        if cmd is None:
            return self._rule['command']
        elif type(cmd) is str:
            raise Exception('commands must be lists, not strings')
        elif 'command' in self._rule:
            raise Exception('command exists in build rule')
        else:
            self._rule['command'] = [ cmd ] 
            return True

    cmd = command
            
    def description(self, des=None):
        if des is None:
            return self._rule['description']
        elif 'description' in self._rule:
            raise Exception('description exists in build rule')
        else:
            self._rule['description'] = des
            return True

    msg = description
    
    def depfile(self, dep=None):
        if dep is None:
            return self._rule['depfile']
        elif 'depfile' in self._rule:
            raise Exception('dep file already specified')
        else:
            self._rule['depfile'] = dep
            return True

    def restat(self):
        self._rule['restat'] = True
        return True

    def rule(self):
        if self._rule['name'] is None:
            raise Exception('Must specify name for rule.')
        else:
            return self._rule

class RuleCloth(object):
    def __init__(self, output=None):
        self.rules = {}
        self.output = None
            
    def add(self, rule):
        if 'name' in rule:
            if 'name' in self.rules:
                raise Exception('Rules must have unique names.')
            else:
                name = rule['name'] 
                del rule['name'] 
                self.rules.update({ name : rule })
        else:
            raise Exception('Rules must have names')
            
    def list_rules(self):
        return [ k for k in self.rules.keys() ]

    def fetch(self, name, block='_all'):
        if self.output == 'ninja':
            return self._ninja(name, block=block)
        elif self.output == 'make':
            return self._make(name, block=block)
        else:
            raise Exception('Must specify output format to BuildRules object.')

    def _make(self, name, block='_all'):
        rule = self.rules[name]

        m = MakefileCloth()
        
        for cmd in rule['command']:
            m.job(cmd, block=block)

        if 'restat' in rule:
            m.job('touch $@', block=block)

        m.msg(rule['description'], block=block)

        if 'depfile' in rule:
            m.raw(['include ' + rule['depfile']], block=block)

        return m.get_block(block)

    def _ninja(self, name, indent=4, block='_all'):
        n = NinjaFileCloth(indent=indent)

        n.rule(name, self.rules[name])
        return n.get_block(block)
