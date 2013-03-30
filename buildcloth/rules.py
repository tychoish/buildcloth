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
"""
:mod:`rules` provides two classes, :class:`~rules.Rule` and
:class:`rules.RuleCloth`, which provide an additional layer of abstraction
between the BuildCloth-described build system and the underlying Ninja or Make
implementation.

:mod:`rules` provides a common interface for both Ninja and Make, but some Ninja
functionality (i.e. restat rules) are not implemented for Make. Additionally,
:mod:`Rule` only describes build rules and does *not* provide a common
abstraction for describing build targets or dependencies.
"""

from buildcloth.makefile import MakefileCloth
from buildcloth.ninja import NinjaFileCloth
from buildcloth.err import InvalidRule, InvalidBuilder

class Rule(object):
    """
    :class:`~rules.Rule()` represents 
    """
    def __init__(self, name=None):
        """
        :param string name: Specifies a name of the rule.

        When initializing you can specify a name for a :class:`~rules.Rule()`
        directly, or you can set it later using :meth:`~rules.Rule.name()`.
        """
        self._rule = { 'name': name }
        "The internal representation of the Rule."

    def name(self, name=None):
        """
        :param string name: Optional. Specifies a name of the rule.
        
        :returns: The name of the :class:`~rules.Rule()` object.

        Sets the name of the :class:`~rules.Rule()` object to ``name``.

        Raises :exc:`~err.InvlaidRule` if you do not specify a name *and* the
        :class:`~rules.Rule()` object doesn't have a name.
        """
        if name is None:
            if 'name' in self._rule:
                if self._rule['name'] is None:
                    raise InvalidRule('Rules must have names.')
                else:
                    return self._rule['name']
            else: 
                raise InvalidRule('Rules must have names.')
        else:
            self._rule['name'] = name
            return name

    def command(self, cmd=None):
        """
        :param list,str cmd: Optional. Specifies a command or sequence of
                             commands that implement the build rule.
        
        :returns: The command list of the :class:`~rules.Rule()` object. If you
                  do not specify a command, and the :class:`~rules.Rule()` does
                  not have a command, :meth:`~rules.Rule.command()` will return
                  ``None``.

        Adds or appends ``cmd`` as a command list to the :class:`~rules.Rule()`
        object.

        Raises :exc:`~err.InvlaidRule` if you do not specify a command list
        *and* the :class:`~rules.Rule()` object doesn't a command list.
        """
        if cmd is None and 'command' in self._rule: 
            return self._rule['command']
        if cmd is None and 'command' not in self._rule: 
            return None
        elif 'command' not in self._rule:
            if type(cmd) is list:
                self._rule['command'] = cmd
            elif type(cmd) is str: 
                self._rule['command'] = [cmd]
            return cmd

    cmd = command
    "An alias for :class:`~rules.Rule.command()`."

    def description(self, des=None):
        """
        :param string des: Optional. The text of the description message that
                           the build job will pass to the user.

        :returns: The current description. 

        :raises: :exc:`~err.InvalidRule` if there is no description set for this rule.
        """
        if des is None and self._rule['description'] is None:
            raise InvalidRule('Rules must have descriptions.')
        elif des is None:
            return self._rule['description']
        else:
            self._rule['description'] = des
            return des

    msg = description
    "An alias for :class:`~rules.Rule.description()`."

    def depfile(self, dep=None):
        """
        :param string dep: Optional. The path to a Makefile that contains
                           dependencies 

        :returns: The current depfile. 

        :raises: :exc:`~err.InvalidRule` if there is no depfile set for this rule.
        """
        if dep is None and self._rule['depfile'] is None:
            raise InvlaidRule('dep file already specified')
        elif  dep is None: 
            return self._rule['depfile']
        else:
            self._rule['depfile'] = dep
            return dep

    def restat(self):
        """
        Sets this rule as a restat rule. This only affects ninja output.

        :returns: ``True``.
        """
        self._rule['restat'] = True
        return True

    def rule(self):
        """
        :returns: A dictionary that contains the full build rule. 

        :raises: :exc:`err.InvalidRule` if you have not specified a name for the
                 builder.
        """

        if self._rule['name'] is None:
            raise InvalidRule('Must specify name for rule.')
        else:
            return self._rule

class RuleCloth(object):
    """
    :class:`~rules.RuleCloth()` provides an interoperable layer between rule
    objects created as :class:`rules.Rule()` objects and build systems generated
    using :class:`~makefile.MakefileCloth()` and
    :class:`~makefile.NinjaFileCloth`.
    """
    def __init__(self, output=None):
        """
        :param string output: Optional. Specifies the output format for the
                              build system. You can specify the output format to
                              the :meth:`~rules.RuleCloth.fetch()` method
                              directly.
        """
        self.rules = {}
        "The structure that represents build rules."

        self.output = None
        "The default build system output format."

    def add(self, rule):
        """
        :param Rule rule: A :class:`~rules.Rule` object. 

        :raises: :exc:`~err.InvalidRule` if the rule doesn't have a name or if
                  the rule already exists in :attr:`~rules.RuleCloth.rules`.

        Adds a :class:`~rules.Rule` object to the :class:`~rules.RuleCloth`
        object. Will not overwrite an existing rule.
        """
        if rule.name() in self.rules:
            raise InvalidRule('Rules must have unique names.')
        else:
            nrule = rule.name()
            drule = rule.rule()
            del drule['name']
            self.rules.update({ nrule : drule })

    def list_rules(self):
        """
        :returns: A list of a the names of all rules that exist in the :class:`~rules.RuleCloth` object.
        """
        return [ k for k in self.rules.keys() ]

    def fetch(self, name, block='_all'):
        """
        :param string name: The name of the build rule in
                            :attr:`~rules.RuleCloth.rules` to return.

        :param string block: Optional; defaults to ``_all``. Specify the name of
                             the block in :attr:`~cloth.BuildCloth.builder` to
                             create and access.

        :returns: The output of :meth:`~cloth.BuildCloth.get_block()` for
                  either Ninja or Makefiles, depending on ``name``.

        :raises: :exc:`~err.InvalidBuilder` when :attr:`~cloth.RuleCloth.output`
                 is neither ``make`` nor ``ninja``.
        """
        if self.output == 'ninja':
            return self._ninja(name, block=block)
        elif self.output == 'make':
            return self._make(name, block=block)
        else:
            raise InvalidBuilder('Must specify output format.')

    def _make(self, name, block='_all'):
        """
        An internal method used by :`~rules.RuleCloth.fetch()` to process
        content from :attr:`~rules.RuleCloth.rules` and return
        :meth:`~cloth.BuildCloth.get_block()` in Makefile format.
        """
        rule = self.rules[name]

        m = MakefileCloth()

        for cmd in rule['command']:
            m.job(cmd, block=block)

        m.msg(rule['description'], block=block)

        if 'depfile' in rule:
            m.raw(['include ' + rule['depfile']], block=block)

        return m.get_block(block)

    def _ninja(self, name, indent=4, block='_all'):
        """
        An internal method used by :`~rules.RuleCloth.fetch()` to process
        content from :attr:`~rules.RuleCloth.rules` and return
        :meth:`~cloth.BuildCloth.get_block()` in Ninja format.
        """
        n = NinjaFileCloth(indent=indent)

        n.rule(name, self.rules[name])
        return n.get_block(block)
