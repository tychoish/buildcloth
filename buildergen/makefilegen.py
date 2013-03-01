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

class MakefileError(BuildFileError):
    pass

class MakefileBuilder(BuildFile):
    def __init__(self, makefile=None):
        super(MakefileBuilder, self).__init__(makefile)
        self.makefile = self.buildfile

    # The following methods constitute the 'public' interface for
    # building makefile.

    def target(self, target, dependency=None, block='_all'):
        if dependency is None:
            self._add_to_builder(target + ':', block)
        else:
            self._add_to_builder(target + ':' + dependency, block)

    def append_var(self, variable, value, block='_all'):
        self._add_to_builder(variable + ' += ' + value, block)

    def job(self, job, display=False, ignore=False, block='_all'):
        o = '\t'
        if display is False:
            o += '@'
        if ignore is True:
            o += '-'
        o += job

        self._add_to_builder(o, block)

    def message(self, message, block='_all'):
        m = 'echo ' + message
        self.job(job=m, display=False, block=block)

    msg = message
