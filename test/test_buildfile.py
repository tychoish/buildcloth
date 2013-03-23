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

from buildcloth.cloth import BuildCloth

from buildcloth.err import (MalformedBlock, DuplicateBlock, MalformedRawContent,
    MalformedContent, InvalidBuilder, MissingBlock)

class TestBuilderRawMethods(TestCase): 
    @classmethod
    def setUp(self):
        self.m = BuildCloth()
        self.content = ['the md5 is ab98a7b91094a4ebd9fc0e1a93e985d6']

    def test_raw_list(self):
        b = 'raw0'
        self.m.raw(lines=self.content, block=b)
       
        self.assertEqual(self.content, self.m.get_block(b))

    def test_raw_string(self):
        b = 'raw1'

        with self.assertRaises(MalformedRawContent):
            self.m.raw(lines=self.content[0], block=b)
        
    def test_raw_nested_list(self):
        b = 'raw2'

        with self.assertRaises(MalformedRawContent):
            self.m.raw(lines=[self.content, self.content], block=b)

class TestBuildClothBlocks(TestCase):
    @classmethod
    def setUp(self):
        self.block = 'ab98'
        self.block1 = '98ab'
        self.b = BuildCloth()
        self.content = 'the md5 is ab98a7b91094a4ebd9fc0e1a93e985d6'

    def test_add_list(self):
        with self.assertRaises(MalformedContent):
            self.b._add_to_builder([self.content, self.content], self.block)

    def test_add_dict(self):
        with self.assertRaises(MalformedContent):
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
