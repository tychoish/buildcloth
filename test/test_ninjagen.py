# Copyright 2012 Sam Kleinman.
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

from unittest import TestCase
from collections import OrderedDict

from buildcloth.ninja import NinjaFileCloth
from buildcloth.cloth import BuildClothError

def munge_lines(line_list):
    i = 0
    for line in line_list:
        line_list[i] = line + '\n'
        i += 1

    return line_list

class TestNinjaBuilderCommentMethods(TestCase):
    @classmethod
    def setUp(self):
        self.n = NinjaFileCloth()
        self.variable = 'var'
        self.value1 = '/a/path/to/nowhere'
        self.value2 = 'bin lib opt srv local usr src'

    def test_var_meth1(self):
        b = 'var1'
        v = self.value1

        self.n.var(self.variable, v, block=b)
        self.assertEqual(self.n.get_block(b)[0], self.variable + ' = ' + v)

    def test_var_meth2(self):
        b = 'var2'
        v = self.value2

        self.n.var(self.variable, v, block=b)
        self.assertEqual(self.n.get_block(b)[0], self.variable + ' = ' + v)

    def test_var_meth3(self):
        b = 'var3'
        v = self.value2

        self.n.var(self.variable, v, block=b)
        self.assertEqual(self.n.get_block(b)[0], self.variable + ' = ' + v)

class TestNinjaBuilderRuleMethods(TestCase):
    @classmethod
    def setUp(self): 
        self.n = NinjaFileCloth(indent=2)
        self.name = 'ruletest'
        self.cmd = 'cat /proc/cpuinfo'
        self.description = 'return info about the cpu'
        self.depfile = 'ruletest.d'
        self.generator = True
        self.restat = True
        self.rsp = ('ruletest.rsp', 'rspfile-file-content-content')
        self.rule_dict = { 'command': [ self.cmd ],
                           'description': self.description,
                           'generator': self.generator,
                           'depfile': self.depfile,
                           'restat': self.restat,
                           'rspfile': self.rsp[0],
                           'rspfile_content': self.rsp[1], 
                           }

        self.rule_dict_simple = { 'command': [ self.cmd ],
                                  'description': self.description
                                }

        with open('test/output/ninja-rule0.txt', 'r') as f:
            self.rule_output = f.readlines()

        with open('test/output/ninja-rule1.txt', 'r') as f:
            self.rule_output_simple = f.readlines()

    def test_ninja_buid(self): 
        block_name = 'test0'
        self.n.rule(self.name, self.rule_dict, block=block_name)
        
        t = munge_lines(self.n.get_block(block_name))

        self.assertEqual(t, self.rule_output)

    def test_basic_ninja_buid(self): 
        block_name = 'test1'
        self.n.rule(self.name, self.rule_dict_simple, block=block_name)
        
        t = munge_lines(self.n.get_block(block_name))

        self.assertEqual(t, self.rule_output_simple)

    def test_ninja_positional_arg_build(self):
        block_name = 'argbuild0'
        
        self.n.add_rule(self.name, self.cmd, self.description, self.depfile,
                        self.generator, self.restat, self.rsp, block=block_name)

        t = munge_lines(self.n.get_block(block_name))

        self.assertEqual(t, self.rule_output)

    def test_ninja_named_arg_build(self):
        block_name = 'argbuild1'
        
        self.n.add_rule(name=self.name, 
                        command=self.cmd, 
                        description=self.description, 
                        depfile=self.depfile,
                        generator=self.generator, 
                        restat=self.restat, 
                        rsp=self.rsp, 
                        block=block_name)

        t = munge_lines(self.n.get_block(block_name))

        self.assertEqual(t, self.rule_output)

    def test_ninja_basic_rule_arg(self):
        block_name = 'argbuild2'
        
        self.n.add_rule(self.name, self.cmd, self.description, block=block_name)

        t = munge_lines(self.n.get_block(block_name))

        self.assertEqual(t, self.rule_output_simple)

    def test_ninja_basic_named_arg_build(self):
        block_name = 'argbuild3'
        
        self.n.add_rule(name=self.name, 
                        command=self.cmd, 
                        description=self.description, 
                        block=block_name)

        t = munge_lines(self.n.get_block(block_name))

        self.assertEqual(t, self.rule_output_simple)

    def test_ninja_named_arg_build(self):
        self.n.add_rule(self.name, self.cmd, self.description, self.depfile,
                        self.generator, self.restat, self.rsp, block='sanity0')

        self.n.add_rule(name=self.name, 
                        command=self.cmd, 
                        description=self.description, 
                        depfile=self.depfile,
                        generator=self.generator, 
                        restat=self.restat, 
                        rsp=self.rsp, 
                        block='sanity1')

        self.assertEqual(self.n.get_block('sanity1'), self.n.get_block('sanity0'))

    def test_multi_command(self):
        block_name = 'multi-line'
        mld = self.rule_dict

        mld['command'].append(self.cmd)
        
        self.n.rule(self.name, self.rule_dict, block=block_name)

        t = self.n.get_block(block_name)

        cmd_line = "  command = " + self.cmd + "; " + self.cmd + "; "
        self.assertEqual(t[1], cmd_line)

    def test_single_command(self):
        block_name = 'single-line'
        sld = self.rule_dict
        
        self.n.rule(self.name, self.rule_dict, block=block_name)
        t = self.n.get_block(block_name)

        cmd_line = "  command = " + self.cmd 
        self.assertEqual(t[1], cmd_line)

    def test_string_cmd(self):
        with self.assertRaises(BuildClothError):
            self.n.rule(self.name, { 'command': 'string' })

class TestNinjaDefault(TestCase):
    @classmethod
    def setUp(self):
        self.n = NinjaFileCloth()

    def test_default(self):
        self.n.default('testrule', block='d0')
        self.assertEqual(['default testrule'], self.n.get_block('d0'))

class TestNinjaBuildMethod(TestCase):
    @classmethod
    def setUp(self):
        self.n = NinjaFileCloth()
        self.path = '/path/to/newark'
        self.rule = 'testrule'
        self.dep = [ 'dep0', 'dep1']
        self.vars = OrderedDict([('dog', 'spot'), ('cat', 'merlin')])
        self.order = [ 'order0', 'order1']
        self.implicit = [ 'implicit', 'pun']

        with open('test/output/ninja-build1.txt', 'r') as f:
            self.build_output_minimal = f.readlines()

        with open('test/output/ninja-build0.txt', 'r') as f:
            self.build_output_maxmial = f.readlines()

    def test_extra_minimal_build(self):
        bname = 'minimal0'
        self.n.build(self.path, self.rule, block=bname)

        t = self.n.get_block(bname)
        self.assertEqual(t, ['build /path/to/newark: testrule'])

    def test_minimal_build(self):
        bname = 'minimal1'
        self.n.build(self.path, self.rule, vars=self.vars, block=bname)

        t = munge_lines(self.n.get_block(bname))
        self.assertEqual(t, self.build_output_minimal)

    def test_maxmal_build(self): 
        bname = 'max0' 
        self.n.build(self.path, self.rule, self.dep, self.vars, 
                     self.order, self.implicit, block=bname)

        t = munge_lines(self.n.get_block(bname))
        self.assertEqual(t, self.build_output_maxmial)

    def test_sanity_args(self):
        self.n.build(self.path, self.rule, self.dep, self.vars, 
                     self.order, self.implicit, block='sanity0')

        self.n.build(path=self.path,
                     rule=self.rule, 
                     dep=self.dep,
                     vars=self.vars, 
                     order_only=self.order,
                     implicit=self.implicit, 
                     block='sanity1')

        self.assertEqual(self.n.get_block('sanity0'), self.n.get_block('sanity1'))

    def test_sanity_args_minimal(self):
        self.n.build(self.path, self.rule, self.dep, block='sanity4')

        self.n.build(path=self.path,
                     rule=self.rule, 
                     dep=self.dep,
                     block='sanity3')

        self.assertEqual(self.n.get_block('sanity3'), self.n.get_block('sanity4'))
