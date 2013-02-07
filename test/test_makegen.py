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

from buildergen import MakefileBuilder
from buildergen.makefilegen import MakefileError

class TestMakefileBuilderRawMethods(TestCase): 
    @classmethod
    def setUp(self):
        self.m = MakefileBuilder()
        self.content = ['the md5 is ab98a7b91094a4ebd9fc0e1a93e985d6']

    def test_raw_list(self):
        b = 'raw0'
        self.m.raw(lines=self.content, block=b)
       
        self.assertEqual(self.content, self.m.get_block(b))

    def test_raw_string(self):
        b = 'raw1'

        with self.assertRaises(MakefileError):
            self.m.raw(lines=self.content[0], block=b)
        
    def test_raw_nested_list(self):
        b = 'raw2'

        with self.assertRaises(MakefileError):
            self.m.raw(lines=[self.content, self.content], block=b)


class TestMakefileBuilderCommentMethods(TestCase):
    @classmethod
    def setUp(self):
        self.m = MakefileBuilder()
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
        self.m = MakefileBuilder()
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

class TestMakefileBuilderVariableMethods(TestCase):
    @classmethod
    def setUp(self):
        self.m = MakefileBuilder()
        self.variable = 'var'
        self.value0 = '$(makepathvar)/build/$(branch)/'
        self.value1 = '$(makepathvar)/archive/$(branch)/'
        self.value2 = 'bin lib opt srv local usr src'

    def test_var_meth1(self):
        b = 'var1'
        v = self.value1

        self.m.var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' = ' + v)

    def test_var_meth2(self):
        b = 'var2'
        v = self.value2

        self.m.var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' = ' + v)

    def test_var_meth3(self):
        b = 'var3'
        v = self.value2

        self.m.var(self.variable, v, block=b)
        self.assertEqual(self.m.get_block(b)[0], self.variable + ' = ' + v)

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
