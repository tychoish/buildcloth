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

from buildcloth.makefile import MakefileCloth
from buildcloth.cloth import BuildCloth
from buildcloth.err  import BuildClothError
class TestInitialMakefile(TestCase):
    @classmethod
    def setUp(self):
        self.argument = [1, 2, 3]
        self.m = MakefileCloth(self.argument)

    def test_list_arguments(self):
        self.assertEqual(self.m.makefile, self.argument)

    def test_makefile_slot(self):
        self.assertEqual(self.m.makefile, self.m.builder['_all'])

    def test_makefile_buildfile(self):
        self.assertEqual(self.m.makefile, self.m.buildfile)


class TestInitialBuildCloth(TestCase):
    @classmethod
    def setUp(self):
        self.argument = [1, 2, 3]
        self.m = BuildCloth(self.argument)

    def test_list_arguments(self):
        self.assertEqual(self.m.buildfile, self.argument)

    def test_makefile_slot(self):
        self.assertEqual(self.m.buildfile, self.m.builder['_all'])

class TestBuildfile(TestCase):
    def test_nested_list_arguments(self):
        argument = [1, ['foo'], 3]

        with self.assertRaises(BuildClothError):
            m = MakefileCloth(argument)

    def test_empty_object(self):
        m = MakefileCloth()
        self.assertEqual(m.makefile, [])
        self.assertEqual(m.builder['_all'], [])

class TestBuildClothInterface(TestCase):
    @classmethod
    def setUp(self):
        self.b = BuildCloth()

    def test_has_get_block(self):
        result = hasattr(self.b, 'get_block')
        self.assertTrue(result)

    def test_has_print_content(self):
        result = hasattr(self.b, 'print_content')
        self.assertTrue(result)

    def test_has_print_block(self):
        result = hasattr(self.b, 'print_block')
        self.assertTrue(result)

    def test_has_write(self):
        result = hasattr(self.b, 'write')
        self.assertTrue(result)

    def test_has_write_block(self):
        result = hasattr(self.b, 'write_block')
        self.assertTrue(result)

class TestMakefileBuilderInterface(TestCase):
    @classmethod
    def setUp(self):
        self.m = MakefileCloth()

    def test_has_block(self):
        result = hasattr(self.m, 'block')
        self.assertTrue(result)

    def test_has_raw(self):
        result = hasattr(self.m, 'raw')
        self.assertTrue(result)

    def test_has_section_break(self):
        result = hasattr(self.m, 'section_break')
        self.assertTrue(result)

    def test_has_comment(self):
        result = hasattr(self.m, 'comment')
        self.assertTrue(result)

    def test_has_newline(self):
        result = hasattr(self.m, 'newline')
        self.assertTrue(result)

    def test_has_var(self):
        result = hasattr(self.m, 'var')
        self.assertTrue(result)

    def test_has_append_var(self):
        result = hasattr(self.m, 'append_var')
        self.assertTrue(result)

    def test_has_job(self):
        result = hasattr(self.m, 'job')
        self.assertTrue(result)

    def test_has_message(self):
        result = hasattr(self.m, 'message')
        self.assertTrue(result)

    def test_has_msg(self):
        self.assertEqual(self.m.msg, self.m.message)
