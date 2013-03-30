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
:mod:`ninja` provides the main interface for managing Makefile output, and is
a thin wrapper around the basic functionality for :class:`~cloth.BuildCloth()`. 
"""

from buildcloth.cloth import BuildCloth
from buildcloth.err import BuildClothError, NinjaClothError, MalformedContent

def process_command(command):
    """
    :param list command: A list of commands.

    Helper function to take a list of commands and transform the command into a
    ``; `` separated list of commands to support multi-operation build
    commands. If ``command`` is not a list, raises
    :exc:`buildcloth.err.MalformedContent`.
    """

    if isinstance(command, str):
        raise MalformedContent('ERROR: ' + command + ' is not a list.')
    elif len(command) == 1:
        cmd = str(command[0])
    else:
        cmd = ''
        for i in command:
            cmd += str(i) + '; '

    return cmd

class NinjaFileCloth(BuildCloth):
    """
    :class:`~ninja.NinjaFileCloth` wraps :class:`~cloth.BuildCloth()` to provide
    an interface for specifying Ninja-based build systems.
    """
    def __init__(self, indent=2, ninjafile=None):
        """
        :param int indent: The number of spaces to indent indented output in
                           ``ninja.build`` output.

        :param NinjaFileCloth ninjafile: A :class:`~ninja.NinjaFileCloth` object
                                         that can seed the current object.

        :class:`~ninja.NinjaFileCloth` initializes objects using
        :class:`~cloth.BuildCloth()`.
        """
        super(NinjaFileCloth, self).__init__(ninjafile)
        self.ninja = self.buildfile
        self.indent = ' ' * indent

    # The following methods constitute the 'public' interface for
    # building ninja.build files.

    def var(self, variable, value, block='_all'):
        """
        :param string variable: The name of the variable.

        :param string value: The value of the variable.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Adds a variable assignment to a build system block.
        """

        self._add_to_builder(variable + ' = ' + value, block)

    def rule(self, name, rule_dict, block='_all'):
        """
        :param string name: The name of the build rule. This string will
                            identify the rule when you specify a builder.

        :param dict rule_dict: A dictionary that contains a complete Ninja build rule.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        :meth:`~ninja.NinjaFileCloth.rule()` parses ``rule_dict`` for the
        following fields and constructs a corresponding ninja rule:

        - ``command`` (required; a list.)
        - ``depfile`` (a path.)
        - ``description``` (required. a string.)
        - ``generator``
        - ``restat``
        - ``rspfile`` (requires corresponding ``rsp_content`` field)

        Internally, :meth:`~ninja.NinjaFileCloth.rule()` wraps
        :meth:`~ninja.NinjaFileCloth.add_rule()`.
        """
        if 'command' not in rule_dict:
            raise MalformedContent('Rules must have commands')

        if 'description' not in rule_dict:
            raise MalformedContent('Rules must have descriptions')

        if not isinstance(rule_dict['description'], str):
            raise MalformedContent('Descriptions must be strings.')

        if 'depfile' in rule_dict:
            depf = rule_dict['depfile']
        else:
            depf = None

        if 'generator' in rule_dict:
            gen = True
        else:
            gen = False

        if 'restat' in rule_dict:
            rstat = True
        else:
            rstat = False

        if 'rspfile' in rule_dict and 'rspfile_content' in rule_dict:
            rsp = ( rule_dict['rspfile'], rule_dict['rspfile_content'] )
        else:
            rsp = None

        if 'restat' in rule_dict:
            rstat = rule_dict['restat']
        else:
            rstat = False

        if 'pool' in rule_dict:
            pool = rule_dict['pool']
        else:
            pool = None

        self.add_rule( name=name,
                       command=rule_dict['command'],
                       description=rule_dict['description'],
                       depfile=depf,
                       generator=gen,
                       restat=rstat,
                       rsp=rsp,
                       pool=pool,
                       block=block
                     )

    def add_rule(self, name, command, description, depfile=None, generator=False,
                 restat=False, rsp=None, pool=None, block='_all'):
        """
        :param string name: Required. Holds the name of the
                            rule. :meth:`~ninja.NinjaFileCloth.build()` targets
                            must refer to a rules using this name.

        :param list command: Required. The shell command or commands. Must
                             present commands as a list, even if there is only one item.

        :param string description: Required. A description of the command's
                                   operation, to be included in Ninja's output.

        ;param string depfile: Optional; defaults to ``None``. Specify a
                               Makefile with dependencies, such as what ``gcc``
                               or other tool chain might generate.

        ;param boolean generator: Optional; defaults to ``False``. Specifies a
                                  special generator rule, signifiying that this
                                  rule generates Ninja files.

        ;param boolean restat: Optional; defaults to ``False``. When ``True``
                               specifies a rule where Ninja will check the
                               ``mtime`` of the file and remove dependencies of
                               this target if the file didn't change.

        ;param tuple rsp: Optional; defaults to disabled. The first value holds
                          the path to the file, and the second value holds the
                          content (typically ``$in``.)

        :param string pool: Optional; defaults to disabled. Specify the name of
                            a worker pool to use for these build targets.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Consider `ninja's rule reference
        <http://martine.github.com/ninja/manual.html#ref_rule>`_ for more
        information about these options.
        """
        o = [ 'rule ' + name ]
        o.append(self.indent + 'command = ' + process_command(command))
        o.append(self.indent + 'description = ' + name.upper() + ' ' + description)

        if depfile is not None:
            o.append(self.indent + 'depfile = ' + depfile)
        if generator is not False:
            o.append(self.indent + 'generator = True')
        if restat is not False:
            o.append(self.indent + 'restat = True')
        if rsp is not None:
            o.append(self.indent + 'rspfile = ' + rsp[0])
            o.append(self.indent + 'rspfile_content = ' + rsp[1])
        if pool is not None:
            o.append(self.indent + 'pool = ' + pool)
        self._add_to_builder(data=o, block=block, raw=True)

    def build(self, path, rule, dep=[], vars={},
              order_only=[], implicit=[], block='_all'):
        """
        :param string path: A path for the build target.

        :param string rule: The name of build rule.

        :param list dep: A list of explicit dependencies.

        :param dict vars: A mapping of variable names to their values.

        :param list order_only: A list of order-only dependencies.

        :param list implicit: A list of implicit dependencies

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Consider `ninja's rule statement reference
        <http://martine.github.com/ninja/manual.html#_build_statements>`_ for
        more information about these options.
        """
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
        """
        :param string rule: The name of the default rule.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        See `ninja's documentation on the default rule
        <http://martine.github.com/ninja/manual.html#_default_target_statements>`_
        for more information.
        """
        self._add_to_builder('default ' + rule, block)

    def phony(self, name, dependency, block='_all'):
        """
        :param string name: The name of a phony rule.

        :param string dependency: The build targets which are "phony."

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        See `ninja's documentation on phony rules
        <http://martine.github.com/ninja/manual.html#_the_tt_phony_tt_rule>`_
        for more information.
        """
        self._add_to_builder('build ' + name + ': phony ' + dependency)

    def pool(self, name, depth, block='_all'):
        """
        :param string name: The name of the worker pool for building

        :param int depth: The size of the worker pool. This cannot exceed the
                          default parallelism specified by ``-j`` to ``ninja``
                          on the command line.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder`.

        Pools provide a way to control and limit concurrency for specific
        jobs. See `ninja's documentation of pools
        <http://martine.github.com/ninja/manual.html#_pools>`_ for more
        information.

        .. note:: Pools are an experimental feature of Ninja that may be
           removed in a future release.
        """
        o = [ 'pool ' + name ]
        o.append(self.indent + 'depth = ' + str(depth))
        self.add_to_builder(data=o, block=block, raw=True)
