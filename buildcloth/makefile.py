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

"""
:mod:`makefile` provides the main interface for managing Makefile output, and is
a thin wrapper around the basic functionality for :class:`~cloth.BuildCloth()`. 
"""

from buildcloth.cloth import BuildCloth
from buildcloth.err import MalformedContent

import sys

if sys.version_info >= (3, 0):
    basestring = str


class MakefileCloth(BuildCloth):
    def __init__(self, makefile=None):
        """
        :class:`~makefile.MakefileCloth` initializes instances using
        :class:`~cloth.BuildCloth()`.
        """
        super(MakefileCloth, self).__init__(makefile)
        self.makefile = self.buildfile
        "An alias for :attr:`~cloth.BuildCloth.buildfile`."

    # The following methods constitute the 'public' interface for
    # building makefile.

    def var(self, variable, value, block='_all'):
        """
        :param string variable: The name of the variable.

        :param string value: The value of the variable.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Adds a variable assignment to a build system block.
        """

        self._add_to_builder(variable + ' = ' + value, block)

    def target(self, target, dependency=None, block='_all'):
        """
        :param string,list target:

           The name of the build target. May be a list of strings of build
           targets or a single string in the form that will appear in the
           Makefile output.

        :param string,list dependency: 

           Optional. Specify dependencies for this build target as either a list
           of targets, or as a string a string in the form that will appear in
           the Makefile output.

        :param string block: 

           Optional; defaults to ``_all``. Specify the name of the block in
           :attr:`~cloth.BuildCloth.builder`.

        Adds a build target to a build system block. You can specify targets and
        dependencies as either strings or as lists of strings. May raise
        :exc:`~err.MalformedContent` if you attempt to add non-string data to a
        builder, or :exc:`~python:TypeError` if a list does not contain strings.
        """
        if isinstance(target, list):
            target = ' '.join(target)

        if not isinstance(target, basestring):
            err = 'Targets must be strings before inserting them to builder.'
            raise MalformedContent(err)

        if dependency is None:
            self._add_to_builder(target + ':', block)
        else:
            if isinstance(dependency, list):
                dependency = ' '.join(dependency)

            if not isinstance(dependency, basestring):
                err = 'Dependencies must be strings before inserting them to builder.'
                raise MalformedContent(err)

            self._add_to_builder(target + ':' + dependency, block)

    def append_var(self, variable, value, block='_all'):
        """
        :param string variable: A string that specifies the name of the variable.

        :param string value: A string that specifies the value of that variable.
        
        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Declare a variable using Make's ``+=`` assignment method. These values
        create or append the ``value`` to the existing value of the variable of
        this name. Unlike Python, in Make, these you may use
        :meth:`~makefile.append_var()` for previously unassigned variables.
        """
        self._add_to_builder(variable + ' += ' + value, block)

    def simple_var(self, variable, value, block='_all'):
        """
        :param string variable: A string that specifies the name of the variable.

        :param string value: A string that specifies the value of that variable.
        
        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Declare a variable using Make's ``:=`` assignment method. These values
        of these variables are expanded once at the time of the creation. By
        default, the value of all other variables in Make are evaluated once
        upon use.
        """
        self._add_to_builder(variable + ' := ' + value, block)
    
    def new_var(self, variable, value, block='_all'):
        """
        :param string variable: A string that specifies the name of the variable.

        :param string value: A string that specifies the value of that variable.
        
        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Declare a variable using Make's ``?=`` assignment method. In Make, these
        variables do not override previous assignments of this variable, whereas
        other assignment methods will override existing values.
        """
        self._add_to_builder(variable + ' ?= ' + value, block)

    def _job(self, job, display=False, ignore=False, block='_all'):
        """
        Internal implementation of :meth:`~makefile.MakefileCloth.job`. To allow
        :meth:`~makefile.MakefileCloth.job()` to handle both list and string
        inputs.
        """
        if isinstance(job, str):
            o = '\t'

            if display is False:
                o += '@'

            if ignore is True:
                o += '-'

            o += job

            self._add_to_builder(o, block)
        else:
            raise MalformedContent('Jobs must all be strings.')
            
    def job(self, job, display=False, ignore=False, block='_all'):
        """
        :param string,list job: The shell command that specifies a job to run to
                                build a target. If you specify a list,
                                :meth:`~makefile.MakefileCloth.job()` will add a
                                sequence of jobs to a builder.

        :param boolean display: Optional; defaults to ``False``. When ``True``
                                Make will output the command when calling it. By
                                default all jobs have an ``@`` prepended,
                                setting this option reverses this behavior.

        :param boolean ignore: Optional; defaults to ``False``. When ``True``,
                               this job will have an ``-`` prepended, which will
                               allow Make to continue building even when this
                               job has a non-zero exit code.
        
        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Creates a shell line or lines (if ``job`` is a list) in a Makefile to
        build a target. May raise :exc:`~err.MalformedContent` ``job`` is not a
        string or list of strings. The ``display`` and ``ignore`` options expose
        underlying Make functionality.
        """

        if isinstance(job, list):
            for j in job:
                self._job(j, display, ignore, block)
        else:
            self._job(job, display, ignore, block)
        
    def include(self, filename, ignore=False, block='_all'):
        """
        :param string filename: The name of the file to include.

        :param boolean ignore: Optional; defaults to ``False``. When ``True``,
                               this job will have an ``-`` prepended, which will
                               allow Make to continue building even when this
                               file exists.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.
        """
        if ignore is True:
            incl = '-include'
        else:
            incl = 'include'

        if isinstance(filename, list):
            for f in filename:
                self._add_to_builder(' '.join([incl, f]), block=block)
        else:
            self._add_to_builder(' '.join([incl, filename]), block=block)



    def message(self, message, block='_all'):
        """
        :param string message: The text of a message to be output by a build
                               process to describe the current state of builds.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.
                             
        :meth:`~makefile.MakefileCloth.message()` is a special wrapper around
        :meth:`~makefile.MakefileCloth.job()` that makes it possible to describe
        the actions of a Make shell line in human-readable text. The buildcloth
        idiom, inspired by ninja is to suppress echoing shell lines to the user
        in favor of crafted messages that describe each action.
        """

        m = 'echo ' + message
        self.job(job=m, display=False, block=block)

    msg = message
    "An alias for :meth:`~makefile.MakefileCloth.message()`"
