# Copyright 2012 10gen, Inc.
# Author: Sam Kleinman (tychoish)
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

from buildergen.buildfile import BuildFile

class MakefileBuilder(BuildFile):
    def __init__(self, makefile=None):
        super(MakefileBuilder, self).__init__(makefile)
        self.makefile = self.buildfile

    # The following two methods allow more direct interaction with the
    # internal representation of the makefile than the other methods.

    def block(self, block):
        if block in self.builder:
            pass
        else:
            self.builder[block] = []
            self.section_break(block, block)

    def raw(self, lines, block='_all'):
        self._add_to_builder(lines, block)

    # The following methods constitute the 'public' interface for
    # building makefile.

    def section_break(self, name, block='_all'):
        self._add_to_builder('\n\n########## ' + name + ' ##########', block)

    def comment(self, comment, block='_all'):
        self._add_to_builder('\n# ' + comment, block)

    def newline(self, n=1, block='_all'):
        for i in range(n):
            self._add_to_builder('\n', block)

    def target(self, target, dependency=None, block='_all'):
        if dependency is None:
            self._add_to_builder(target + ':', block)
        else:
            self._add_to_builder(target + ':' + dependency, block)

    def var(self, variable, value, block='_all'):
        self._add_to_builder(variable + ' = ' + value, block)

    def append_var(self, variable, value, block='_all'):
        self._add_to_builder(variable + ' += ' + value, block)

    def job(self, job, display=False, block='_all'):
        if display is True:
            o = '\t' + job
        else:
            o = '\t@' + job

        self._add_to_builder(o, block)

    def message(self, message, block='_all'):
        m = 'echo ' + message
        self.job(job=m, display=False, block=block)

    msg = message
