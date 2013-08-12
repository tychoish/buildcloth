from buildcloth.system import BuildSystem, BuildSystemGenerator
from buildcloth.stages import BuildStage, BuildSequence, BuildSteps
from buildcloth.err import InvalidStage, StageClosed, InvalidSystem, StageRunError
from test.utils import dummy_function, dump_args_to_json_file, dump_args_to_json_file_with_newlines
from unittest import TestCase
import json
import os 

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

    def test_closed_property0(self):
        self.assertEqual(self.bs.closed, not self.bs.open)

    def test_close(self):
        self.assertFalse(self.bs.closed)

    def test_strict_property(self):
        self.assertTrue(self.bs.strict)
    
    def test_strict_property_set(self):
        self.bs.strict = False
        self.assertFalse(self.bs.strict)
        self.bs.strict = True

    def test_strict_property_validation(self):
        self.bs.strict = 1
        self.assertTrue(self.bs.strict)

    def test_close_action(self):
        self.bs.close()
        self.assertFalse(self.bs.open)

        # campfire rule testing
        self.bs.open = True

    def test_close_close(self):
        self.bs.close()
        self.assertFalse(self.bs.open)
        self.bs.close()
        self.assertFalse(self.bs.open)

        # campfire rule testing
        self.bs.open = True

    def test_vaidation_valid_case(self):
        valid = self.bs._validate_stage('test')
        self.assertTrue(valid)
        
    def test_vaidation_invalid_case(self):
        self.bs.add_stage(name='test', stage_type='seq')
        print self.bs.stages
        valid = self.bs._validate_stage('test')
        self.assertFalse(valid)
        
    def test_new_stage(self):
        self.bs.new_stage('test0')
        self.assertTrue('test0' in self.bs.stages)

    def test_extend_stage(self):
        b = BuildSystem()
        stages = ['test1', 'test2', 'test3']
        for i in stages:
            b.new_stage(i)

        self.bs.extend(b)

        for i in stages:
            self.assertTrue(i in self.bs.stages)

    def test_extend_stage_error(self):
        with self.assertRaises(InvalidSystem):
            self.bs.extend(object())

    def test_adding_stage_none(self):
        self.bs.add_stage('test4')
        self.assertTrue('test4' in self.bs.stages)
        self.assertTrue(isinstance(self.bs.stages['test4'], BuildStage))

    def test_adding_stage_seq_type(self):
        self.bs.add_stage('test5', stage_type='seq')
        self.assertTrue('test5' in self.bs.stages)
        self.assertTrue(isinstance(self.bs.stages['test5'], BuildSequence))

    def test_adding_stage_sequence_type(self):
        self.bs.add_stage('test6', stage_type='seq')
        self.assertTrue('test6' in self.bs.stages)
        self.assertTrue(isinstance(self.bs.stages['test6'], BuildSequence))

    def test_adding_stage_stage(self):
        self.bs.add_stage('test7', stage_type='stage')
        self.assertTrue('test7' in self.bs.stages)
        self.assertTrue(isinstance(self.bs.stages['test7'], BuildStage))

    def test_adding_invalid_stage_type_strict(self):
        with self.assertRaises(InvalidStage):
            self.bs.add_stage('test8', stage_type='foo')

    def test_adding_invalid_stage_obj_strict(self):
        with self.assertRaises(InvalidStage):
            self.bs.add_stage('test9', stage=object())

    def test_adding_invalid_stage_type(self):
        self.assertFalse(self.bs.add_stage('test10', stage_type='foo', strict=False))

    def test_adding_invalid_stage_obj(self):
        self.assertFalse(self.bs.add_stage('test11', stage=object(), strict=False))

    def test_add_stage_return_value(self):
        self.assertTrue(self.bs.add_stage('test12'))

    def test_error_or_return_perm(self):
        self.assertFalse(self.bs._error_or_return(msg='test', strict=False))

    def test_error_or_return_strict(self):
        with self.assertRaises(InvalidSystem):
            self.assertFalse(self.bs._error_or_return(msg='test', strict=True))

    def test_error_or_return_default(self):
        self.bs.strict = True
        with self.assertRaises(InvalidSystem):
            self.assertFalse(self.bs._error_or_return(msg='test'))

    def test_return_type_order(self):
        self.assertTrue(isinstance(self.bs.get_order(), list))

    def test_order(self):
        stages = ['test13', 'test14', 'test15']
        for i in stages:
            self.bs.new_stage(i)

        self.assertEqual(self.bs.get_order(), stages)

    def test_order_index(self):
        stages = ['test16', 'test17', 'test18']
        for i in stages:
            self.bs.new_stage(i)

        idx = 2
        self.assertEqual(self.bs.get_stage_index(stages[idx]), idx)

    def test_stage_count(self):
        stages = ['test19', 'test20', 'test21']
        for i in stages:
            self.bs.new_stage(i)

        self.assertEqual(self.bs.count(), len(stages))

    def test_stage_exists(self):
        stages = ['test22', 'test23', 'test24']
        for i in stages:
            self.bs.new_stage(i)

        self.assertTrue(self.bs.stage_exists(stages[2]))

    def test_stage_not_extant(self):
        stages = ['test25', 'test26', 'test27']
        for i in stages:
            self.bs.new_stage(i)

        self.assertFalse(self.bs.stage_exists('toast'))

class TestSystemRunStage(TestCase):
    @classmethod
    def setUp(self):
        self.bs = BuildSystem()

        self.a = {'a': 'value'}
        self.b = {'b': 1 * 10 }

        job = BuildStage()
        job.add(dump_args_to_json_file, (self.a, self.b))

        self.bs.add_stage('test', job)

    def test_run_non_existing_stage_strict_defalut(self):
        with self.assertRaises(StageRunError):
            self.bs.run_stage('nope')

    def test_run_non_existing_stage_strict_explicit(self):
        with self.assertRaises(StageRunError):
            self.bs.run_stage('nope', strict=True)

    def test_run_non_existing_stage_permissive(self):
        self.assertFalse(self.bs.run_stage('nope', strict=False))

    def test_run_stage_with_open_system(self):
        self.assertTrue(self.bs.open)
        self.assertEqual(len(self.bs.stages), 1)

        self.assertTrue(self.bs.run_stage('test'))

        with open('t', 'r') as f:
            t = json.load(f)
            
            self.assertEqual(t, [self.a, self.b])

        os.remove('t')
        
        self.assertFalse(os.path.exists('t'))

    def test_run_stage_with_closed_system(self):
        self.assertTrue(self.bs.open)

        self.bs.close()

        self.assertFalse(self.bs.open)
        self.assertEqual(len(self.bs.stages), 1)
        
        self.assertTrue(self.bs.run_stage('test'))

        with open('t', 'r') as f:
            t = json.load(f)
            
            self.assertEqual(t, [self.a, self.b])

        os.remove('t')

        self.assertFalse(os.path.exists('t'))

class ComplexSystem(TestCase):
    @classmethod
    def setUp(self):
        self.bs = BuildSystem()

        self.a = {'a': 1 }
        self.b = {'b': 'string'}
        self.c = {'c': 'string' * 4 }
        self.d = {'d': 10 * 4 }

        self.fn_one = 'one.json'
        self.fn_two = 'two.json'
        self.fn_three = 'three.json'
        self.fn_four = 'four.json'

        job_one = BuildStage()
        job_two = BuildStage()
        job_three = BuildStage()
        job_four = BuildStage()
        
        job_one.add(dump_args_to_json_file_with_newlines, (self.a, self.b, self.fn_one))
        job_one.add(dump_args_to_json_file_with_newlines, (self.d, self.c, self.fn_one))
        job_one.add(dummy_function, (self.a, self.b))
        job_one.add(dummy_function, (self.a, self.c))
        
        job_two.add(dump_args_to_json_file_with_newlines, (self.a, self.b, self.fn_two))
        job_two.add(dump_args_to_json_file_with_newlines, (self.c, self.d, self.fn_two))
        job_two.add(dummy_function, (self.a, self.c))
        job_two.add(dummy_function, (self.a, self.d))

        job_three.add(dump_args_to_json_file_with_newlines, (self.c, self.b, self.fn_three))
        job_three.add(dump_args_to_json_file_with_newlines, (self.a, self.d, self.fn_three))
        job_three.add(dummy_function, (self.a, self.b))
        job_three.add(dummy_function, (self.a, self.c))

        job_four.add(dump_args_to_json_file_with_newlines, (self.a, self.a, self.fn_four))
        job_four.add(dump_args_to_json_file_with_newlines, (self.a, self.b, self.fn_four))
        job_four.add(dummy_function, (self.a, self.c))

        self.bs.add_stage('one', job_one)
        self.bs.add_stage('two', job_two)
        self.bs.add_stage('three', job_three)
        self.bs.add_stage('four', job_four)

    @classmethod
    def tearDown(self):
        for fn in [ self.fn_one, self.fn_two, self.fn_three, self.fn_four ]:
            if os.path.exists(fn):
                os.remove(fn)

    def unwind_json_from_outputs(self, fn):
        with open(fn, 'r') as f:
            data = list()
            for ln in f.readlines():
                d = json.loads(ln)

                for i in d:
                    data.append(i)
        
        return data

class TestSystemRunPart(ComplexSystem):
    def test_run_part_non_existing_stage_strict_default(self):
        self.assertTrue(self.bs.open)
        self.assertTrue(self.bs.strict)
        with self.assertRaises(StageRunError):
            self.bs.run_part(20)

    def test_run_part_non_existing_stage_strict_explict(self):
        self.assertTrue(self.bs.open)
        self.assertTrue(self.bs.strict)
        with self.assertRaises(StageRunError):
            self.bs.run_part(20, strict=True)

    def test_run_part_non_existing_stage_closed_strict(self):
        self.assertTrue(self.bs.open)
        self.bs.close()
        self.assertFalse(self.bs.open)
        self.assertTrue(self.bs.strict)
        with self.assertRaises(StageRunError):
            self.bs.run_part(20, strict=True)

    def test_run_part_non_existing_stage_closed_permissive_explict(self):
        self.assertTrue(self.bs.open)
        self.bs.close()
        self.assertFalse(self.bs.open)
        self.assertFalse(self.bs.run_part(20, strict=False))

    def test_run_part_non_existing_stage_closed_permissive_implicit(self):
        self.assertTrue(self.bs.open)
        self.bs.close()
        self.assertFalse(self.bs.open)
        self.bs.strict = False
        self.assertFalse(self.bs.strict)
        self.assertFalse(self.bs.run_part(20))
        self.bs.strict = True
        self.bs.open = True

    def test_run_part_success(self):
        self.assertTrue(self.bs.open)
        self.bs.close()
        self.assertFalse(self.bs.open)
        self.bs.strict = False
        self.assertFalse(self.bs.strict)

        self.assertTrue(self.bs.run_part(2))
        self.bs.strict = True

    def test_run_part_success(self):
        self.assertTrue(self.bs.open)
        self.bs.close()
        self.assertFalse(self.bs.open)

        self.assertTrue(self.bs.strict)
        with self.assertRaises(StageRunError):
            self.bs.run_part(-1)

class TestSystemRunPartLimits(ComplexSystem):
    def test_run_part_success_not_overbuilt(self):
        self.assertTrue(self.bs.open)
        self.bs.close()
        self.assertFalse(self.bs.open)
        self.bs.strict = False
        self.assertFalse(self.bs.strict)

        if os.path.exists(self.fn_three):
            os.remove(self.fn_three)

        self.assertTrue(self.bs.run_part(2))

        self.assertTrue(os.path.exists(self.fn_two))
        self.assertFalse(os.path.exists(self.fn_three))

        self.bs.strict = True

    def test_part_off_by_one_potential(self):
        self.bs.close()
        self.assertTrue(self.bs.run_part(self.bs.count()))

class TestSystemRunAllTestOutput(ComplexSystem):
    def test_output_one(self):
        self.bs.close()
        self.assertTrue(self.bs.run())
        self.assertEqual(self.unwind_json_from_outputs(self.fn_one), 
                         [self.a, self.b, self.d, self.c])

    def test_output_two(self):
        self.bs.close()
        self.assertTrue(self.bs.run())
        self.assertEqual(self.unwind_json_from_outputs(self.fn_two), 
                         [self.a, self.b, self.c, self.d])
        
    def test_output_three(self):
        self.bs.close()
        self.assertTrue(self.bs.run())
        self.assertEqual(self.unwind_json_from_outputs(self.fn_three), 
                         [self.c, self.b, self.a, self.d])

    def test_output_four(self):
        self.bs.close()
        self.assertTrue(self.bs.run())
        self.assertEqual(self.unwind_json_from_outputs(self.fn_four), 
                         [self.a, self.a, self.a, self.b])

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
