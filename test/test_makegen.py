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

from buildcloth import MakefileCloth
from buildcloth.err import MalformedContent
        
class TestMakefileBuilderMessageMethods(TestCase):
    @classmethod
    def setUp(self):
        self.m = MakefileCloth()
        self.content = 'the md5 is ab98a7b91094a4ebd9fc0e1a93e985d6'
        self.output = ['\t@echo ' + self.content ]

    def test_msg_meth(self):
        b = 'msg1'
        self.m.msg(self.content, block=b)

        self.assertEqual(self.output, self.m.get_block(b))

    def test_message_meth(self):
        b = 'message1'
        self.m.message(self.content, block=b)

        self.assertEqual(self.output, self.m.get_block(b))

    def test_message_interface(self):
        self.m.message(self.content, block='message1')
        self.m.msg(self.content, block='msg1')

        self.assertIsNot(self.m.get_block('message1'), self.m.get_block('msg1'))
        self.assertEqual(self.m.get_block('message1'), self.m.get_block('msg1'))
        self.assertEqual(self.m.get_block('msg1') + self.m.get_block('message1'), self.m.builder['_all'])

class TestMakefileBuilderJobMethod(TestCase):
    @classmethod
    def setUp(self):
        self.m = MakefileCloth()
        self.job = 'git update-index --assume-unchanged'
        self.job_make = '\t' + self.job
        self.job_quiet = '\t@' + self.job
        self.job_ignore = '\t-' + self.job
        self.job_quiet_ignore = '\t@-' + self.job

    def test_job_default(self):
        self.m.job(self.job, block='test')
        self.assertEqual(self.m.get_block('test')[0], self.job_quiet)

    def test_job_ignored_named(self):
        self.m.job(self.job, ignore=True, block='test')
        self.assertEqual(self.m.get_block('test')[0], self.job_quiet_ignore)

    def test_job_ignored_positional(self):
        self.m.job(self.job, False, True, block='test')
        self.assertEqual(self.m.get_block('test')[0], self.job_quiet_ignore)

    def test_job_unquiet_named(self):
        self.m.job(self.job, display=True, block='test')
        self.assertEqual(self.m.get_block('test')[0], self.job_make)

    def test_job_unquiet_positional(self):
        self.m.job(self.job, True, block='test')
        self.assertEqual(self.m.get_block('test')[0], self.job_make)

    def test_job_unquiet_ignored_positional(self):
        self.m.job(self.job, True, True, block='test')
        self.assertEqual(self.m.get_block('test')[0], self.job_ignore)

    def test_job_unquiet_ignored_named(self):
        self.m.job(self.job, display=True, ignore=True, block='test')
        self.assertEqual(self.m.get_block('test')[0], self.job_ignore)

    def test_job_invalid_dict_job(self):
        with self.assertRaises(MalformedContent):
            self.m.job({'a': 'string'}, block='test')

    def test_job_invalid_num(self):
        with self.assertRaises(MalformedContent):
            self.m.job(1, block='test')

    def test_job_invalid_nested_list(self):
        with self.assertRaises(MalformedContent):
            self.m.job([ 'a', [ 'a', '1'] ], block='test')

    def test_job_list(self):
        jobs = ['a', 'b']
        builder = ['\t@a', '\t@b']

        self.m.job(jobs, block='job-list')
        self.assertEqual(self.m.get_block('job-list'), builder)

class TestTargetsAndDependencies(TestCase):
    @classmethod
    def setUp(self):
        self.m = MakefileCloth()
        self.block = 'test-block'

    def test_target_invalid_dict_target(self):
        with self.assertRaises(MalformedContent):
            self.m.target({'a': 'string'}, block='test')

    def test_target_invalid_num_target(self):
        with self.assertRaises(MalformedContent):
            self.m.target(1, block='test')

    def test_target_invalid_dict_dep(self):
        with self.assertRaises(MalformedContent):
            self.m.target('a', {'a': 'string'}, block='test')

    def test_target_invalid_num_dep(self):
        with self.assertRaises(MalformedContent):
            self.m.target('a', 1, block='test')

    def test_target_single_no_dep(self):
        target = 'a'
        result = ['a:']

        self.m.target(target, block=self.block)
        self.assertEqual(self.m.get_block(self.block), result)

    def test_target_single_with_dep(self):
        target = 'a'
        dep = 'b'
        result = ['a:b']

        self.m.target(target, dep, block=self.block)
        self.assertEqual(self.m.get_block(self.block), result)

    def test_target_single_no_dep(self):
        target = 'a'
        result = ['a:']

        self.m.target(target, block=self.block)
        self.assertEqual(self.m.get_block(self.block), result)

    def test_target_single_with_dep(self):
        target = 'a'
        dep = 'b'
        result = ['a:b']

        self.m.target(target, dep, block=self.block)
        self.assertEqual(self.m.get_block(self.block), result)

    def test_target_multi_no_dep(self):
        target = ['a', 'b' ]
        result = ['a b:']

        self.m.target(target, block=self.block)
        self.assertEqual(self.m.get_block(self.block), result)

    def test_target_multi_with_dep(self):
        target = ['a', 'b' ]
        dep = 'c'
        result = ['a b:c']

        self.m.target(target, dep, block=self.block)
        self.assertEqual(self.m.get_block(self.block), result)

    def test_target_multi_with_multi_dep(self):
        target = ['a', 'b' ]
        dep = ['c', 'd' ]
        result = ['a b:c d']

        self.m.target(target, dep, block=self.block)
        self.assertEqual(self.m.get_block(self.block), result)

    def test_target_single_with_multi_dep(self):
        target = 'a'
        dep = ['b', 'c']
        result = ['a:b c']

        self.m.target(target, dep, block=self.block)
        self.assertEqual(self.m.get_block(self.block), result)









        

class TestMakefileClothVariableMethods(TestCase):
    @classmethod
    def setUp(self):
        self.m = MakefileCloth()
        self.variable = 'var'
        self.value0 = '$(makepathvar)/build/$(branch)/'
        self.value1 = '$(makepathvar)/archive/$(branch)/'
        self.value2 = 'bin lib opt srv local usr src'

    def test_append_var_meth1(self):
        b = 'append_var1'
        v = self.value1

        self.m.append_var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' += ' + v)

    def test_var_meth2(self):
        b = 'append_var2'
        v = self.value2

        self.m.append_var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' += ' + v)

    def test_var_meth3(self):
        b = 'append_var3'
        v = self.value2

        self.m.append_var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' += ' + v)

    def test_new_var_meth1(self):
        b = 'new_var1'
        v = self.value1

        self.m.new_var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' ?= ' + v)

    def test_new_var_meth2(self):
        b = 'new_var2'
        v = self.value2

        self.m.new_var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' ?= ' + v)

    def test_new_var_meth3(self):
        b = 'new_var3'
        v = self.value2

        self.m.new_var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' ?= ' + v)

    def test_simple_var_meth1(self):
        b = 'simple_var1'
        v = self.value1

        self.m.simple_var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' := ' + v)

    def test_simple_var_meth2(self):
        b = 'simple_var2'
        v = self.value2

        self.m.simple_var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' := ' + v)

    def test_simple_var_meth3(self):
        b = 'simple_var3'
        v = self.value2

        self.m.simple_var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' := ' + v)



        
