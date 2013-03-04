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

from unittest import TestCase

from buildcloth.rules import Rule, RuleCloth

class TestRule(TestCase):
    @classmethod
    def setUp(self):
        self.r = Rule()
        self.name = 'rulenametest'
        self.description = 'this is message text'
        self.command = ['cat foo | grep']
        self.depfile = 'output.d'

        self.example_rule = { 'name' : self.name,
                              'description': self.description,
                              'command': self.command,
                              'depfile': self.depfile }
             
    def test_rule_return(self):
        self.r.name(self.name)
        self.r.description(self.description)
        self.r.command(self.command)
        rule = self.r.rule()

        self.assertEqual(type(rule), type(self.example_rule))

    def test_rule_has_keys(self):
        self.r.name(self.name)
        self.r.description(self.description)
        self.r.command(self.command)
        self.r.depfile(self.depfile)
        rule = self.r.rule()

        self.assertEqual(rule.keys(), self.example_rule.keys())

class TestRuleName(TestCase):
    @classmethod
    def setUp(self):
        self.r = Rule()
        self.name = 'rulenametest'

    def test_default_name(self):
        self.assertEqual(self.r._rule['name'], None)

    def test_name_requirement(self):
        with self.assertRaises(Exception):
            self.r.name()
    
    def test_add_name_helper(self):
        self.r.name(self.name)
        self.assertEqual(self.name, self.r._rule['name'])

    def test_return_name_helper(self):
        self.r.name(self.name)
        self.assertEqual(self.r.name(), self.name)

    def test_name_return_value(self):
        self.assertTrue(self.r.name(self.name))
        
class TestRuleCommand(TestCase):
    @classmethod
    def setUp(self):
        self.r = Rule()
        self.command = ['cat foo | grep']

    def test_command_helper(self):
        self.r.command(self.command)
        self.assertEqual([self.command] , self.r._rule['command'])

    def test_command_immutable(self):
        self.r.command(self.command)

        with self.assertRaises(Exception):
            self.r.command(self.command + 'a change')

    def test_default_command_state(self):
        with self.assertRaises(KeyError):
            self.r.command()

    def test_cmd_command_alias(self):
        self.assertEqual(self.r.cmd, self.r.command)

    def test_command_return_helper(self):
        self.r.command(self.command)
        self.assertEqual([self.command] , self.r.command())

    def test_command_return_value(self):
        self.assertTrue(self.r.command(self.command))

    def test_command_string(self):
        with self.assertRaises(Exception): 
            self.r.command('a string')

class TestRuleDescription(TestCase):
    @classmethod
    def setUp(self):
        self.r = Rule()
        self.description = 'this is message text'

    def test_description_return_value(self):
        self.assertTrue(self.r.description(self.description))
 
    def test_msg_description_alias(self):
        self.assertEqual(self.r.msg, self.r.description)

    def test_description_helper(self):
        self.r.description(self.description)
        self.assertEqual(self.description , self.r._rule['description'])

    def test_description_immutable(self):
        self.r.description(self.description)

        with self.assertRaises(Exception):
            self.r.description(self.description + 'change')

    def test_default_description_state(self):
        with self.assertRaises(KeyError):
            self.r.description()

    def test_description_return_helper(self):
        self.r.description(self.description)
        self.assertEqual(self.description , self.r.description())

class TestRuleDepFile(TestCase):
    @classmethod
    def setUp(self):
        self.r = Rule()
        self.depfile = 'output.d'

    def test_depfile_return_value(self):
        self.assertTrue(self.r.depfile(self.depfile))
 
    def test_depfile_helper(self):
        self.r.depfile(self.depfile)
        self.assertEqual(self.depfile , self.r._rule['depfile'])

    def test_depfile_immutable(self):
        self.r.depfile(self.depfile)

        with self.assertRaises(Exception):
            self.r.depfile(self.depfile + 'change')

    def test_default_depfile_state(self):
        with self.assertRaises(KeyError):
            self.r.depfile()

    def test_depfile_return_helper(self):
        self.r.depfile(self.depfile)
        self.assertEqual(self.depfile , self.r.depfile())
 
class TestRuleRestat(TestCase):
    @classmethod
    def setUp(self):
        self.r = Rule()

    def test_restat_return_value(self):
        self.assertTrue(self.r.restat())

    def test_restat_exists(self):
        self.r.restat()
        self.assertTrue(self.r.restat())

    def test_rule_without_name(self):
        with self.assertRaises(Exception):
            self.r.rule()

class TestBuildRules(TestCase):
    @classmethod
    def setUp(self):
        self.rdb = RuleCloth()
        self.rule_name = 'ccompile'
        self.example_rule = { 'name': self.rule_name, 'description': 'compile $file', 'command': ['cc $in'] }

    def test_add_rule_in_list(self):
        self.rdb.add(self.example_rule)
        self.assertTrue('ccompile' in self.rdb.list_rules())
    
    def test_add_rule_without_name(self):
        rule = self.example_rule
        del rule['name']

        with self.assertRaises(Exception):
            self.rd.add(rule)
            
    def test_add_rule_with_same_name(self):
        self.rdb.add(self.example_rule)
        with self.assertRaises(Exception):
            self.rdb.add(self.example_rule)

    def test_add_rule_without_name(self):
        self.rdb.add(self.example_rule)
        self.assertFalse('name' in self.rdb.rules[self.rule_name])

    def test_invalid_output_type(self):
        self.rdb.output = 'scons'
        self.rdb.add(self.example_rule)

        with self.assertRaises(Exception):
            self.rdb.fetch(self.rule_name)

    def test_ninja_fetch_output(self):
        self.rdb.output = 'ninja'
        self.rdb.add(self.example_rule)

        ninja_rule = ['rule ccompile', '    command = cc $in', '    description = CCOMPILE compile $file']
        self.assertEqual(self.rdb.fetch(self.rule_name), ninja_rule)

    def test_make_fetch_output(self):
        self.rdb.output = 'make'
        self.rdb.add(self.example_rule)

        make_rule = ['\t@cc $in', '\t@echo compile $file']
        self.assertEqual(self.rdb.fetch(self.rule_name), make_rule)

