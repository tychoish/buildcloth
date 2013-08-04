from unittest import TestCase
from buildcloth.stages import BuildSteps, BuildStage, BuildSequence, BuildSystem, BuildSystemGenerator
from buildcloth.err import InvalidStage, StageClosed
from multiprocessing import cpu_count
from pickle import PicklingError
import json
import os

def dump_args_to_json_file(a=None, b=None):
    with open('t', 'a') as f:
        json.dump((a,b), f)

def dummy_function(a=None, b=None):
    return a, b

class StagesBuildStepTests(object):
    def test_initiated_obj(self):
        self.assertEqual(len(self.b.stage), 0)

    def test_closed_setting(self):
        self.assertFalse(self.b.closed)
        self.assertTrue(self.b._open)

    def test_close_action(self):
        self.b.close()
        self.assertFalse(self.b._open)
        self.assertTrue(self.b.closed)

    def test_double_close_action(self):
        self.b.close()
        self.assertFalse(self.b._open)
        self.assertTrue(self.b.closed)

        self.b.close()
        self.assertFalse(self.b._open)
        self.assertTrue(self.b.closed)

    def test_default_worker(self):
        self.assertEqual(cpu_count, self.b.workers)

    def test_workers_floor_threshold_0(self):
        self.b.workers = 1
        self.assertEqual(2, self.b.workers)

    def test_workers_floor_threshold_1(self):
        self.b.workers = 0
        self.assertEqual(2, self.b.workers)

    def test_workers_floor_threshold_2(self):
        self.b.workers = -1
        self.assertEqual(2, self.b.workers)

    def test_workers_set_value(self):
        tworkers = cpu_count() * 2

        self.b.workers = tworkers
        self.assertEqual(self.b.workers, tworkers)

    def test_validate_tuple_args(self):
        ret = self.b.validate( (cpu_count, ('a', 'b')) )
        self.assertTrue(ret)

    def test_validate_list_args(self):
        ret = self.b.validate( (cpu_count, ['a', 'b']) )
        self.assertTrue(ret)

    def test_validate_dict_args(self):
        ret = self.b.validate( (cpu_count, { 'a': 'b' } ) )
        self.assertTrue(ret)

    def test_validate_invalid_lenght_perm_implicitly(self):
        ret = self.b.validate( (cpu_count, ) )
        self.assertFalse(ret)

    def test_validate_invalid_lenght_perm_explicitly(self):
        ret = self.b.validate( (cpu_count, ), strict=False )
        self.assertFalse(ret)

    def test_validate_invalid_lenght_strict(self):
        with self.assertRaises(InvalidStage):
            ret = self.b.validate( (cpu_count, ), strict=True )

    def test_validate_invalid_not_func_strict(self):
        with self.assertRaises(InvalidStage):
            ret = self.b.validate( (None, None), strict=True )

    def test_validate_invalid_arg_string_strict_0(self):
        with self.assertRaises(InvalidStage):
            ret = self.b.validate( (cpu_count, 1), strict=True )

    def test_validate_invalid_arg_string_strict_1(self):
        with self.assertRaises(InvalidStage):
            ret = self.b.validate( (cpu_count, 'a'), strict=True )

    def test_validate_invalid_not_func_perm_explict(self):
        ret = self.b.validate( (None, None), strict=False )

    def test_validate_invalid_arg_string_perm_0_explict(self):
        ret = self.b.validate( (cpu_count, 1), strict=False )

    def test_validate_invalid_arg_string_perm_1_explict(self):
        ret = self.b.validate( (cpu_count, 'a'), strict=False )

    def test_validate_invalid_not_func_perm_implicit(self):
        ret = self.b.validate( (None, None) )

    def test_validate_invalid_arg_string_perm_0_implicit(self):
        ret = self.b.validate( (cpu_count, 1) )

    def test_validate_invalid_arg_string_perm_1_implicit(self):
        ret = self.b.validate( (cpu_count, 'a') )

    def test_add_strict_implict(self):
        job = (cpu_count, (1,))

        self.b.add(*job)
        self.assertEqual(self.b.stage[0], job)

    def test_add_strict_explicit(self):
        job = (cpu_count, (1,))

        self.b.add(*job, strict=True)
        self.assertEqual(self.b.stage[0], job)

    def test_add_perm(self):
        job = (cpu_count, (1,))

        self.b.add(*job, strict=False)
        self.assertEqual(self.b.stage[0], job)

    def test_add_to_closed_strict_implict(self):
        job = (cpu_count, (1,))

        self.b.close()
        with self.assertRaises(StageClosed):
            self.b.add(*job)

    def test_add_to_closed_strict_explicit(self):
        job = (cpu_count, (1,))

        self.b.close()

        with self.assertRaises(StageClosed):
            self.assertFalse(self.b.add(*job, strict=True))

    def test_add_to_closed_perm(self):
        job = (cpu_count, (1,))

        self.b.close()
        self.assertFalse(self.b.add(*job, strict=False))

    def test_add_invalid_strict_implict(self):
        job = (None, (1,))

        with self.assertRaises(InvalidStage):
            self.b.add(*job)

    def test_add_invalid_strict_explicit(self):
        job = (None, (1,))

        with self.assertRaises(InvalidStage):
            self.b.add(*job, strict=True)

    def test_add_invalid_perm(self):
        job = (None, (1,))

        self.assertFalse(self.b.add(*job, strict=False))

    def test_add_invalid_to_closed_strict_implict(self):
        job = (None, (1,))

        self.b.close()
        with self.assertRaises(StageClosed):
            self.b.add(*job)

    def test_add_invalid_to_closed_strict_explicit(self):
        job = (None, (1,))

        self.b.close()
        with self.assertRaises(StageClosed):
            self.assertFalse(self.b.add(*job, strict=True))

    def test_add_invalid_to_closed_perm(self):
        job = (None, (1,))

        self.b.close()
        self.assertFalse(self.b.add(*job, strict=False))

    def test_stage_count(self):
        self.b.grow(dummy_function, [ (1,2), (3, 4) ])
        self.assertEqual(self.b.count(), 2)

class TestStagesBuildSteps(StagesBuildStepTests, TestCase):
    @classmethod
    def setUp(self):
        self.b = BuildSteps()

    def test_run(self):
        with self.assertRaises(NotImplementedError):
            self.b.run()

class TestStagesBuildStage(StagesBuildStepTests, TestCase):
    @classmethod
    def setUp(self):
        self.b = BuildStage()
        self.args = [ [1, 2], [2, 3], [1, 5], [8, 9] ]
        self.result = ''.join([ str(i) for i in self.args ])

    def test_running(self, a=None, b=None):
        for arg in self.args:
            self.b.add(dump_args_to_json_file, [arg[0], arg[1]])

        self.b.run()

        with open('t', 'r') as f:
            jsn = f.read()

        self.assertEqual(sorted(self.result), sorted(jsn))

    @classmethod
    def tearDown(self):
        if os.path.exists('t'):
            os.remove('t')

class TestStagesBuildSequence(StagesBuildStepTests, TestCase):
    @classmethod
    def setUp(self):
        self.b = BuildSequence()
        self.args = [ (1, 2), (2, 3), (1, 'str'), ('str', 'str') ]
        self.results = []

    def t_function(self, a=None, b=None):
        self.results.append((a, b))

    def test_running(self):
        for arg in self.args:
            self.b.add(self.t_function, [arg[0], arg[1]])

        self.b.run()
        self.assertEqual(self.results, self.args)

class StagesBuildStepMultiAddTests(object):
    def test_valid_test_harness(self):
        self.assertEqual( self.jobs[0][1], self.args[0] )

    def sanatize(self):
        self.b.stage = []
        self.bs.stage = []

    def test_extend(self):
        self.b.extend(self.jobs)

        for func, args in self.jobs:
            self.bs.add(func, args)

        self.assertEqual(self.b.stage, self.bs.stage)
        self.sanatize()

    def test_extend_strict_explict(self):
        self.b.extend(self.jobs, strict=True)
        for func, args in self.jobs:
            self.bs.add(func, args, strict=True)

        self.assertEqual(self.b.stage, self.bs.stage)
        self.sanatize()

    def test_grow(self):
        self.b.grow(dummy_function, self.args)
        for arg in self.args:
            self.bs.add(dummy_function, arg)

        self.assertEqual(self.b.stage, self.bs.stage)
        self.sanatize()

    def test_grow_strict_explicit(self):
        self.b.grow(dummy_function, self.args, strict=True)
        for arg in self.args:
            self.bs.add(dummy_function, arg, strict=True)

        self.assertEqual(self.b.stage, self.bs.stage)
        self.sanatize()

class TestStagesBuildStepsMultiAdd(StagesBuildStepMultiAddTests, TestCase):
    @classmethod
    def setUp(self):
        self.jobs = [ (cpu_count, (1, 2)), (dummy_function, ('str', 'str')) ]
        self.args = [ (1, 2), (2, 3), (1, 'str'), ('str', 'str') ]

        self.b = BuildSteps()
        self.bs = BuildSteps()

class TestStagesBuildStageMultiAdd(StagesBuildStepMultiAddTests, TestCase):
    @classmethod
    def setUp(self):
        self.jobs = [ (cpu_count, (1, 2)), (dummy_function, ('str', 'str')) ]
        self.args = [ (1, 2), (2, 3), (1, 'str'), ('str', 'str') ]

        self.b = BuildStage()
        self.bs = BuildStage()

class TestStagesBuildSequenceMultiAdd(StagesBuildStepMultiAddTests, TestCase):
    @classmethod
    def setUp(self):
        self.jobs = [ (cpu_count, (1, 2)), (dummy_function, ('str', 'str')) ]
        self.args = [ (1, 2), (2, 3), (1, 'str'), ('str', 'str') ]

        self.b = BuildSequence()
        self.bs = BuildSequence()

class TestStagesBuildSystem(TestCase):
    pass

class TestStagesBuildSystemGenerator(TestCase):
    pass
