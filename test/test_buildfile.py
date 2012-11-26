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

from buildergen.buildfile import BuildFile
from buildergen.buildfile import BuildFileError

class TestBuildFileBlocks(TestCase):
    @classmethod
    def setUp(self):
        self.block = 'ab98'
        self.block1 = '98ab'
        self.b = BuildFile()
        self.content = 'the md5 is ab98a7b91094a4ebd9fc0e1a93e985d6'

    def test_add_list(self):
        with self.assertRaises(BuildFileError):
            self.b._add_to_builder([self.content, self.content], self.block)

    def test_add_dict(self):
        with self.assertRaises(BuildFileError):
            self.b._add_to_builder({ self.block: self.content }, self.block)

    def test_block_in_builder(self):
        self.b._add_to_builder(self.content, self.block)

        self.assertIn(self.block, self.b.builder)

    def test_add_content_to_block(self):
        self.b._add_to_builder(self.content, self.block)

        self.assertEqual([self.content], self.b.builder['_all'])
        self.assertEqual([self.content], self.b.builder[self.block])
        self.assertIsNot([self.content], self.b.builder[self.block])
        self.assertEqual(self.b.builder[self.block], self.b.builder['_all'])

    def test_add_content_to_different_blocks(self):
        self.b._add_to_builder(self.content, self.block)
        self.b._add_to_builder(self.content, self.block1)
        b_block = self.b.get_block(self.block)
        b_block1= self.b.get_block(self.block1)

        self.assertEqual(b_block, b_block1)
        self.assertIsNot(b_block, b_block1)
        self.assertEqual(b_block + b_block1, self.b.builder['_all'])
