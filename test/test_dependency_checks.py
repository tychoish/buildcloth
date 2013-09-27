from buildcloth.err import DependencyCheckError
from buildcloth.dependency import DependencyChecks
from unittest import TestCase, skip
import sys
import os
import time

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def write(fname, content):
    with open(fname, 'w') as f:
        f.write(content)

def breath():
    if sys.platform == 'darwin':
        time.sleep(0.25)
    else:
        time.sleep(0.01)

class TestDependencyChecking(TestCase):
    @classmethod
    def setUp(self):
        self.d = DependencyChecks()
        self.fn_a = 'fn_a'
        self.fn_b = 'fn_b'

    @classmethod
    def tearDown(self):
        for fn in [ self.fn_a, self.fn_b ]:
            if os.path.exists(fn):
                os.remove(fn)

    def ensure_clean(self):
        self.assertFalse(os.path.exists(self.fn_a))
        self.assertFalse(os.path.exists(self.fn_b))

    def test_basic(self):
        self.ensure_clean()
        touch(self.fn_a)
        self.assertTrue(os.path.exists(self.fn_a))
        self.assertFalse(os.path.exists(self.fn_b))

    def test_basic_alt(self):
        self.ensure_clean()
        touch(self.fn_b)
        self.assertTrue(os.path.exists(self.fn_b))
        self.assertFalse(os.path.exists(self.fn_a))

    def test_default_method(self):
        self.ensure_clean()
        self.assertTrue(self.d.check_method, 'mtime')

    def test_setting_valid_methods(self):
        self.ensure_clean()
        for method in ['force', 'ignore', 'hash', 'mtime']:
            self.d.check_method = method

            self.assertTrue(self.d.check_method, method)

        self.d.check_method = 'mtime'
        self.assertTrue(self.d.check_method, 'mtime')

    def test_setting_invalid_method(self):
        self.ensure_clean()
        with self.assertRaises(DependencyCheckError):
            self.d.check_method = 'magic'

    def test_mtime_rebuild(self):
        self.ensure_clean()

        touch(self.fn_a)
        breath()
        touch(self.fn_b)

        self.assertTrue(self.d.check_method, 'mtime')
        self.assertTrue(self.d.check(self.fn_a, self.fn_b))

    def test_mtime_no_rebuild(self):
        self.ensure_clean()

        touch(self.fn_b)
        breath()
        touch(self.fn_a)

        self.assertTrue(self.d.check_method, 'mtime')
        self.assertFalse(self.d.check(self.fn_a, self.fn_b))

    def test_mtime_rebuild_no_target(self):
        self.ensure_clean()

        touch(self.fn_b)

        self.assertTrue(self.d.check_method, 'mtime')
        self.assertTrue(self.d.check(self.fn_a, self.fn_b))

    def test_hash_rebuild(self):
        self.ensure_clean()

        write(self.fn_a, 'aaa')
        write(self.fn_b, 'bbb')

        self.d.check_method = 'hash'
        self.assertTrue(self.d.check_method, 'hash')
        self.assertTrue(self.d.check(self.fn_a, self.fn_b))

    def test_hash_rebuild_ignoring_update_order(self):
        self.ensure_clean()

        write(self.fn_b, 'bbb')
        breath()
        breath()
        write(self.fn_a, 'aaa')

        self.d.check_method = 'hash'
        self.assertTrue(self.d.check_method, 'hash')
        self.assertTrue(self.d.check(self.fn_a, self.fn_b))

    def test_hash_no_rebuild(self):
        self.ensure_clean()

        write(self.fn_b, 'aaa')
        write(self.fn_a, 'aaa')

        self.d.check_method = 'hash'
        self.assertTrue(self.d.check_method, 'hash')
        self.assertFalse(self.d.check(self.fn_a, self.fn_b))

    def test_hash_rebuild_no_target(self):
        self.ensure_clean()

        write(self.fn_b, 'aa')

        self.d.check_method = 'hash'
        self.assertTrue(self.d.check_method, 'hash')
        self.assertTrue(self.d.check(self.fn_a, self.fn_b))

    def test_force_non_existing(self):
        self.ensure_clean()
        self.d.check_method = 'force'
        self.assertTrue(self.d.check_method, 'force')
        self.assertTrue(self.d.check(self.fn_a, self.fn_b))

    def test_force_with_files(self):
        self.ensure_clean()

        touch(self.fn_a)
        breath()
        touch(self.fn_b)

        self.d.check_method = 'force'
        self.assertTrue(self.d.check_method, 'force')
        self.assertTrue(self.d.check(self.fn_a, self.fn_b))

    def test_force_with_reversed_files(self):
        self.ensure_clean()

        touch(self.fn_b)
        breath()
        touch(self.fn_a)

        self.d.check_method = 'force'
        self.assertTrue(self.d.check_method, 'force')
        self.assertTrue(self.d.check(self.fn_a, self.fn_b))

    def test_ignore_non_existing(self):
        self.ensure_clean()
        self.d.check_method = 'ignore'
        self.assertTrue(self.d.check_method, 'ignore')
        self.assertFalse(self.d.check(self.fn_a, self.fn_b))

    def test_ignore_with_files(self):
        self.ensure_clean()

        touch(self.fn_a)
        breath()
        touch(self.fn_b)

        self.d.check_method = 'ignore'
        self.assertTrue(self.d.check_method, 'ignore')
        self.assertFalse(self.d.check(self.fn_a, self.fn_b))

    def test_ignore_with_reversed_files(self):
        self.ensure_clean()

        touch(self.fn_b)
        breath()
        touch(self.fn_a)

        self.d.check_method = 'ignore'
        self.assertTrue(self.d.check_method, 'ignore')
        self.assertFalse(self.d.check(self.fn_a, self.fn_b))
