# Copyright 2013 Sam Kleinman
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

"""
:mod:`dependency` provides a set of tools for checking if dependencies need to
be rebuilt. :class:`~dependency.DependencyChecks` provides a flexible interface
to this dependency checking.
"""

from buildcloth.err import DependencyCheckError
from buildcloth.utils import is_function
import inspect
import hashlib
import logging
import os

logger = logging.getLogger(__name__)

def mtime_check(target, dependency):
    """
    :param path target: The path to a file to build.

    :param path dependency: The path of a file to that the ``target`` depends
       upon.

    :returns: ``True`` if ``target`` has a larger *mtime* than the ``dependency``.
    """
    if os.stat(target).st_mtime < os.stat(dependency).st_mtime:
        return True
    else:
        return False

def md5_file_check(file, block_size=2**20):
    """
    :param path file: The path to a file.

    :param int blocksize: The size of the block size for the hashing
       process. Defaults to ``2**20`` or ``1048576``.

    :returns: The md5 checkusm of ``file``.
    """

    md5 = hashlib.md5()

    with open(file, 'rb') as f:
        for chunk in iter(lambda: f.read(128*md5.block_size), b''):
            md5.update(chunk)

    return md5.hexdigest()

def hash_check(target, dependency):
    """
    :param path target: The path to a file to build.

    :param path dependency: The path of a file to that the ``target`` depends
       upon.

    :returns: ``True`` if ``target`` and ``dependency`` have different md5
       checksums as determined by :func:`~dependency.md5_file_check()`.
    """

    if md5_file_check(target) != md5_file_check(dependency):
        return True
    else:
        return False

class DependencyChecks(object):
    def __init__(self, check=None):
        """
        :class:`~`

        :param check: Specify an initial dependency checking method.
        """
        members = inspect.getmembers(self, inspect.ismethod)

        self.checks = {}
        """A dictionary mapping the kinds of dependency checks to the functions
        that implement the dependency test."""

        for member in members:
            if is_function(member[1]):
                if member[1].__name__.startswith('_'):
                    pass
                else:
                    self.checks[member[0]] = member

        if check is None and 'mtime' in self.checks:
            self._check = 'mtime'
            """The current default dependency check. Defaults to ``mtime`` if it
            exists, otherwise uses the first available method."""
        else:
            self._check = members[0][0]

    @property
    def check_method(self):
        """
        Property of the current dependency checking method. Returns the string
        identifier of the current dependency checking method.

        If set to ``None``, reverts :attr:`~dependency.DependencyChecks._check`
        to the default value (i.e. ``mtime`` if exists it or the first available
        method.). Otherwise only permits setting
        :attr:`~dependency.DependencyChecks._check` to an existing method, and
        raises :exc:`~err.DependencyCheckError` otherwise.
        """
        return self._check

    @check_method.setter
    def check_method(self, value):
        if value is None:
            if 'mtime' in self.checks:
                self._check = 'mtime'
            else:
                self._check = insepect.getmembers(self, inspect.ismethod)[0][0]
        elif value != 'check' and value in self.checks:
            self._check = value
        else:
            raise DependencyCheckError('{0} does not exist'.format(value))

    def force(self, target, dependency):
        """
        :param path target: The path to a file to check.

        :param path dependency: The path or list of paths of files that the ``target`` depends
           upon.

        :returns: ``True`` always.
        """
        return True

    def ignore(self, target, dependency):
        """
        :param path target: The path to a file to check.

        :param path dependency: The path or list of paths of files that the ``target`` depends
           upon.

        :returns: ``False`` always.
        """
        return False

    def mtime(self, target, dependency):
        """
        :param path target: The path to a file to check.

        :param path dependency: The path or list of paths of files that the ``target`` depends
           upon.

        :returns: ``True`` when ``dependency`` or any members of a
           ``dependency`` list are newer than ``target``.
        """

        if not os.path.exists(target) and not os.path.islink(target):
            return True

        if isinstance(dependency, list):
            for dep in dependency:
                if mtime_check(target, dep) is True:
                    return True
                else:
                    continue
        else:
            return mtime_check(target, dependency)

    def hash(self, target, dependency):
        """
        :param path target: The path to a file to check.

        :param path dependency: The path or list of paths of files that the ``target`` depends
           upon.

        :returns: ``True`` when ``dependency`` or any members of a
           ``dependency`` list have a different md5 checkusm than ``target``.
        """

        if not os.path.exists(target) and not os.path.islink(target):
            return True

        if isinstance(dependency, list):
            for dep in dependency:
                if hash_check(target, dep) is True:
                    return True
                else:
                    continue
        else:
            return hash_check(target, dependency)

    def check(self, target, dependency):
        """
        :param path target: The path to a file to check.

        :param path dependency: The path or list of paths of files that the ``target`` depends
           upon.

        :returns: ``True`` or ``False`` depending on the result of dependency
           check specified by :attr:`~dependency.DependencyChecks._check`.
        """
        logger.debug('running dependency check ({0}), of target {1} on dependency {2}'.format(self._check, target, dependency))
        test = self.checks[self._check][1](target, dependency)
        logger.info('rebuild check {0} result: {1} for target {2}'.format(self._check, test, target))

        return test
