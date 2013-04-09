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
:mod:`cloth` holds the core Buildcloth functions that generate output, and
handle the internal representation of the build file output.
"""

from buildcloth.err import ( MalformedBlock, DuplicateBlock,
    MalformedRawContent, MalformedContent, InvalidBuilder, MissingBlock)

import os

def print_output(list):
    """
    :param list list: A list of strings to print.

    Takes a list as a single argument and prints each line.
    """
    for line in list:
        print(line)

def write_file(list, filename):
    """
    :param list list: A list of strings to write.
    :param string filename: The name of the file to write with ``list``.

    Write all items in ``list`` to the file specified by ``filename``. Creates
    enclosing directories if needed, and overwrite an existing file of the same
    name if it exists.
    """
    dirpath = filename.rsplit('/', 1)[0]
    if os.path.isdir(dirpath) is False:
        os.mkdir(dirpath)

    with open(filename, 'w') as f:
        for line in list:
            f.write(line + '\n')

class BuildCloth(object):
    """
    The primary base class for a generated build system file. Contains an
    interface for producing output, as well as the structure for representing
    build system fragments internally.

    :class:`~cloth.BuildCloth` have a notion of :term:`block <block>`, or
    sections of a makefile, identified by keys in the
    :attr:`~cloth.BuildCloth.builder` dictionary. All items are always added to
    the ``_all`` key, which is the default block, but you can optionally add
    data to other ``blocks`` if you want to insert build specifications out of
    order. Nevertheless, :class:`~cloth.BuildCloth` is not thread-safe.
    """

    def __init__(self, buildfile=None):
        """
        :param BuildCloth buildfile: An object of the :class:`~cloth.BuildCloth` class.

        By default, :class:`~cloth.BuildCloth` creates an empty
        :class:`~cloth.BuildCloth` object. However, if you pass a
        :class:`~cloth.BuildCloth` object or list buildfile lines, the new
        :class:`~cloth.BuildCloth` object will add these lines to the ``_all``
        block.

        Raises :exc:`~err.MalformedBlock` if ``buildfile`` is not a list, or
        if ``buildfile`` is a list or a dict.
        """

        self.builder = { '_all' : [] }
        """The main mapping of :term:`block` names to block content, which are
        lists of lines of build systems. The ``_all`` key stores all block
        content, somewhat redundantly."""

        self.buildfile = self.builder['_all']
        "An alias to the ``_all`` block of :attr:`~cloth.BuildCloth.builder`."

        if buildfile is None:
            pass
        elif type(buildfile) is list:
            for line in buildfile:
                if type(line) is list or type(line) is dict:
                    raise MalformedBlock('Cannot instantiate BuildCloth with nested list or dictionary.')
                    break
                else:
                    self.builder['_all'].append(line)
        else:
            raise MalformedBlock('Instantiated BuildCloth object with malformed argument.')

    # The following two methods allow more direct interaction with the
    # internal representation of the buildfile.

    def block(self, block, cloth=[]):
        """
        :param string block: The name of a build file block to create.

        :param list cloth: Optional; defaults to an empty block. The content of
                        a build cloth block to insert.

        Raises a :exc:`~err.DuplicateBlock` error if the block exists, otherwise
        creates a new empty block, or a block containing the content of the
        ``cloth`` value.
        """

        if block in self.builder:
            raise DuplicateBlock('Cannot add "%s" to build. %s already exists.'
                                 % (block, block))
        else:
            self.builder[block] = cloth

    def raw(self, lines, block='_all'):
        """
        :param list lines: A list of strings used as lines inserted directly to
                           buildfile blocks.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Adds raw content to the buildfile representation, useful for inserting
        build systems constructs not present in Buildcloth such as ``ifdef``
        statements in :term:`Makefiles <makefile>`.

        Raises :exc:`~err.MalformedRawContent` if you attempt to add non-list
        content or a list that contains lists or dicts.
        """

        if type(lines) is list:
            o = []
            for line in lines:
                if type(line) is list or type(line) is dict:
                    raise MalformedRawContent('Cannot add nested lists or dicts with raw().')
                else:
                    o.append(line)
            self._add_to_builder(data=o, block=block, raw=True)
        else:
            raise MalformedRawContent('Cannot add non-list raw() content.')

    # Basic commenting and other formatting niceties that are not builder
    # specific but are generally userfacing.

    def section_break(self, name, block='_all'):
        """
        :param string name: The name of the section.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Adds an item to a block that consists of 2 blank lines a series of
        octothorpe characters (e.g. ``#``), the ``name`` and more octothrope
        characters. Use section breaks to increase the readability of output
        build systems.
        """
        self._add_to_builder('\n\n########## ' + name + ' ##########', block)

    def comment(self, comment, block='_all'):
        """
        :param string comment: The text of a comment.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Adds an item to a block that consists of a blank line, a single
        octothorpe and the text of the ``comment``. Use comments to increase
        readability and explictness of the build system.
        """
        self._add_to_builder('\n# ' + comment, block)

    def newline(self, n=1, block='_all'):
        """
        :param int n: Defaults to ``1``.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Appends new empty strings to a block, which the output methods render as
        blank lines.
        """

        for i in range(n):
            self._add_to_builder('', block)

    # the following method is used internally to construct and
    # maintain the internal representation of the buildfile.

    def _add_to_builder(self, data, block, raw=False):
        """
        Internal interface used to append content to a block, used by all other
        methods to modify the content of a buildfile. Do not call directly: use
        :meth:`~cloth.BuildCloth.raw()` to add content directly.

        May raise :exc:`~err.BuildCloth.MalformedContent()` in cases when
        a user attempts to add non-string data to the build file.
        """
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
        elif type(data) is not str:
            raise MalformedContent('Avoided adding malformed data to BuildCloth.')
        else:
            add(data, block)

    # The following methods produce output for public use.

    def get_block(self, block='_all'):
        """
        :param string block: The name of a block in :attr:`~cloth.BuildCloth.builder`.

        Returns the content of the block in :attr:`~cloth.BuildCloth.builder`
        specified by ``block``. Used for testing and integration with other
        Python code.

        If ``block`` does not exist in :attr:`~cloth.BuildCloth.builder`,
        :meth:`~cloth.BuildCloth.get_block()` raises :exc:`~err.InvalidBuilder`.
        """
        if block not in self.builder:
            raise MissingBlock('Error: ' + block + ' not specified in buildfile')
        else:
            return self.builder[block]

    def print_content(self, block_order=['_all']):
        """
        :param list block_order: Defaults to ``['_all']``. Must be a
                                 list. Specifies the list of order to return
                                 blocks in.

        Print blocks in :attr:`~cloth.BuildCloth.builder`, in the order
        specified by ``block_order``. Use for testing or output to standard output.

        Use :meth:`~cloth.BuildCloth.write()` to write content to


        """

        output = []

        if type(block_order) is not list:
            raise InvalidBuilder('Cannot print blocks not specified as a list.')
        else:
            for block in block_order:
                output.append(self.builder[block])

            output = [item for sublist in output for item in sublist]
            print_output(output)

    def print_block(self, block='_all'):
        """
        :param string block: The name of a block in
                             :attr:`~cloth.BuildCloth.builder`.

        Prints a single named block. use for testing and writing block content
        to standard output.

        If ``block`` does not exist in :attr:`~cloth.BuildCloth.builder`,
        :meth:`~cloth.BuildCloth.print_block()` raises
        :exc:`~err.MissingBlock`.
        """
        if block not in self.builder:
            raise MissingBlock('Error: ' + block + ' not specified in buildfile')
        else:
            print_output(self.builder[block])

    def write(self, filename, block_order=['_all']):
        """
        :param string filename: The path of a file to write
                                :attr:`~cloth.BuildCloth.builder` builder content to.

        :param list block_order: Defaults to ``['_all']``. Must be a
                                 list. Specifies the list of order to return
                                 blocks in.

        Uses :meth:`~cloth.write_file()`. In default operation,
        :meth:`~cloth.BuildCloth.write()`
        :meth:`~cloth.BuildCloth.write_block()` have the same output.
        :meth:`~cloth.BuildCloth.write()` makes it possible to write a sequence
        of :term:`blocks <block>`.
        """

        output = []

        if type(block_order) is not list:
            raise MissingBlock('Cannot write blocks not specified as a list.')
        else:
            for block in block_order:
                output.append(self.builder[block])

            output = [item for sublist in output for item in sublist]
            write_file(output, filename)

    def write_block(self, filename, block='_all'):
        """
        :param string filename: The path of a file to write
                                :attr:`~cloth.BuildCloth.builder` content to.

        :param string block: The name of a :attr:`~cloth.BuildCloth.builder`
                             :term:`block`.

        Uses :meth:`~cloth.write_file()`. In default operation,
        :meth:`~cloth.BuildCloth.write()`
        :meth:`~cloth.BuildCloth.write_block()` have the same output.
        :meth:`~cloth.BuildCloth.write_block()` makes it possible to write a
        single :term:`block`.
        """

        if block not in self.builder:
            raise MissingBlock('Error: ' + block + ' not specified in buildfile')
        else:
            write_file(self.builder[block], filename)
