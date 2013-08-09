from buildcloth.system import BuildSystem, BuildSystemGenerator
from buildcloth.stages import BuildStage, BuildSequence, BuildSteps
from buildcloth.err import InvalidStage, StageClosed
from test.utils import dummy_function
from unittest import TestCase

class TestBuildSystem(TestCase):
    @classmethod
    def setUp(self):
        self.bs = BuildSystem()

    def test_init_stages_value(self):
        self.assertTrue(isinstance(self.bs.stages, dict))

    def test_init_open(self):
        self.assertTrue(self.bs.open)

    def test_init_empty_stages(self):
        self.assertEqual(self.bs.count(), 0)

    def test_init_with_stages(self):
        b_one = BuildStage()
        b_two = BuildSequence()

        bs_one = BuildSystem()
        bs_one.add_stage('one', b_one)
        bs_one.add_stage('two', b_two)

        bs_two = BuildSystem(bs_one)

        self.assertEqual(bs_two.count(), bs_one.count())
        self.assertEqual(bs_two.get_order(), bs_one.get_order())

class TestBuildSystemGenerator(TestCase):
    @classmethod
    def setUp(self):
        self.bsg = BuildSystemGenerator()

    def test_inititation_funcs_empty(self):
        self.assertEqual(self.bsg.funcs, {})

    def test_inititation_funcs_initialized(self):
        func = { 'a': dummy_function }
        bs = BuildSystemGenerator(func)
        self.assertEqual(bs.funcs, func)

    def test_inititation_funcs_initialized_tuple(self):
        func = ('a', dummy_function)
        bs = BuildSystemGenerator(func)
        self.assertEqual(bs.funcs, {})

    def test_inititation_internal_stages(self):
        self.assertTrue(isinstance(self.bsg._stages, BuildSystem))

    def test_inititation_empty_system(self):
        self.assertEqual(self.bsg.system, None)
