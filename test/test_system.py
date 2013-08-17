from buildcloth.system import BuildSystem, BuildSystemGenerator
from buildcloth.stages import BuildStage, BuildSequence, BuildSteps
from buildcloth.dependency import DependencyChecks
from buildcloth.err import InvalidStage, StageClosed, InvalidSystem, StageRunError, InvalidJob
from test.utils import dummy_function, dump_args_to_json_file, dump_args_to_json_file_with_newlines
from unittest import TestCase, skip
import subprocess
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
    def result_assertion(self, fn, result):
        self.assertEqual([ item.items() for item in self.unwind_json_from_outputs(fn)].sort(),
                         [ item.items() for item in result].sort())

    def test_output_one(self):
        self.bs.close()
        self.assertTrue(self.bs.run())
        self.result_assertion(self.fn_one, [self.a, self.b, self.d, self.c])

    def test_output_two(self):
        self.bs.close()
        self.assertTrue(self.bs.run())
        self.result_assertion(self.fn_two, [self.a, self.b, self.c, self.d])

    def test_output_three(self):
        self.bs.close()
        self.assertTrue(self.bs.run())
        self.result_assertion(self.fn_three, [self.c, self.b, self.a, self.d])

    def test_output_four(self):
        self.bs.close()
        self.assertTrue(self.bs.run())
        self.result_assertion(self.fn_four, [self.a, self.a, self.a, self.b])

class TestBuildSystemGeneratorShellJob(TestCase):
    @classmethod
    def setUp(self):
        self.bsg = BuildSystemGenerator()
        self.ex_args = { 'cmd': 'go',
                    'cwd': '/tmp/test',
                    'args': ['test', 'true']}
        self.expected = (subprocess.call, self.ex_args)

    def assertions_abs_path(self, ret):
        self.assertEquals(ret[0], self.expected[0])
        self.assertEquals(self.ex_args['cmd'], ret[1]['args'][0])
        self.assertEquals(self.ex_args['cwd'], ret[1]['cwd'])
        self.assertEquals(self.ex_args['args'], ret[1]['args'][1:])

    def assertions_rel_path(self, ret):
        ex_path = os.path.join(os.path.abspath(self.ex_args['cwd'][1:]))

        self.assertEquals(ret[0], self.expected[0])
        self.assertEquals(self.ex_args['cmd'], ret[1]['args'][0])
        self.assertEquals(ex_path, ret[1]['cwd'])
        self.assertEquals(self.ex_args['args'], ret[1]['args'][1:])

    def test_generate_shell_job_list_args(self):
        ret = self.bsg.generate_shell_job({ 'cmd': 'go', 'args': ['test', 'true'], 'dir': '/tmp/test'})

        self.assertions_abs_path(ret)

    def test_generate_shell_job_string_args(self):
        ret = self.bsg.generate_shell_job({ 'cmd': 'go', 'args': 'test true', 'dir': '/tmp/test'})

        self.assertions_abs_path(ret)

    def test_generate_shell_job_list_path(self):
        ret = self.bsg.generate_shell_job({ 'cmd': 'go', 'args': 'test true', 'dir': ['/tmp', 'test']})

        self.assertions_abs_path(ret)

    def test_generate_shell_job_list_path_list_args(self):
        ret = self.bsg.generate_shell_job({ 'cmd': 'go', 'args': ['test', 'true'], 'dir': ['/tmp', 'test']})

        self.assertions_abs_path(ret)

    def test_generate_shell_job_list_path_rel_path_list_args(self):
        ret = self.bsg.generate_shell_job({ 'cmd': 'go', 'args': ['test', 'true'], 'dir': ['tmp', 'test']})

        self.assertions_rel_path(ret)

    def test_generate_shell_job_list_path_rel_path_string_args(self):
        ret = self.bsg.generate_shell_job({ 'cmd': 'go', 'args': 'test true', 'dir': ['tmp', 'test']})

        self.assertions_rel_path(ret)

class TestBuildSystemSequenceGeneration(TestCase):
    @classmethod
    def setUp(self):
        self.bsg = BuildSystemGenerator()

        self.sequence = BuildSequence()

        self.funcs = { 'dumb': dummy_function,
                       'dump_new': dump_args_to_json_file_with_newlines,
                       'dump': dump_args_to_json_file,
                       'shell': subprocess.call }

    def test_generate_sequence(self):
        self.sequence.add(dummy_function, (1, 2))
        self.sequence.add(dump_args_to_json_file, ('tmp', 'test'))
        self.sequence.add(dummy_function, (1, 2))
        self.sequence.add(dummy_function, (1, 2))
        self.sequence.add(dump_args_to_json_file, ('tmp', 'test'))
        self.sequence.add(dummy_function, (1, 2))
        self.sequence.add(subprocess.call, (1, 2, 3, 4))

        spec = { 'tasks': [ { 'job': dummy_function, 'args': [1, 2 ] },
                            { 'job': dump_args_to_json_file, 'args': ['tmp', 'test']},
                            { 'job': dummy_function, 'args': [1, 2 ] },
                            { 'job': dummy_function, 'args': [1, 2 ] },
                            { 'job': dump_args_to_json_file, 'args': ['tmp', 'test']},
                            { 'job': dummy_function, 'args': [1, 2 ] },
                            { 'job': subprocess.call, 'args': [1, 2, 3, 4] } ],
                 'stage': 'test'}

        ret = self.bsg.generate_sequence(spec, self.funcs)

        self.assertEqual(ret.stage, self.sequence.stage)

    def test_generate_sequence_shell_job(self):
        self.sequence.add(dummy_function, (1, 2))
        self.sequence.add(subprocess.call, dict(cwd='/tmp', args=['test', 1, 2, 3]))

        spec = { 'tasks': [ { 'job': dummy_function, 'args': [1, 2 ] },
                            { 'cmd': "test",
                              'dir': '/tmp',
                              'args': [1, 2, 3] } ],
                 'stage': 'test'}

        ret = self.bsg.generate_sequence(spec, self.funcs)

        self.assertEqual(ret.stage, self.sequence.stage)


    def test_invalid_spec(self):
        with self.assertRaises(InvalidStage):
            self.bsg.generate_sequence({'stage': 'cmd', 'job': None}, self.funcs)

    def test_invalid_spec_task(self):
        with self.assertRaises(InvalidStage):
            self.bsg.generate_sequence({'stage': 'cmd', 'task': None}, self.funcs)

    def test_invalid_spec_tasks_type(self):
        with self.assertRaises(InvalidStage):
            self.bsg.generate_sequence({'stage': 'cmd', 'tasks': 'string'}, self.funcs)

    def test_generated_sequence_is_closed(self):
        spec = { 'tasks': [ { 'job': dummy_function, 'args': [1, 2 ] },
                            { 'cmd': "test",
                              'dir': '/tmp',
                              'args': [1, 2, 3] } ],
                 'stage': 'test'}

        ret = self.bsg.generate_sequence(spec, self.funcs)

        self.assertTrue(ret.closed)

class TestBuildGeneratorProcessStageSpecs(TestCase):
    @classmethod
    def setUp(self):
        self.bsg = BuildSystemGenerator()
        self.bsg.add_task('dumb', dummy_function)
        self.bsg.add_task('dumb_json', dump_args_to_json_file)
        self.bsg.add_task('dumb_json_newline', dump_args_to_json_file_with_newlines)
        self.bsg.add_task('shell', subprocess.call)

        self.funcs = { 'dumb': dummy_function,
                       'dump_json_newline': dump_args_to_json_file_with_newlines,
                       'shell': subprocess.call,
                       'dumb_json': dump_args_to_json_file }

        self.strings = { 'is': 'is not',
                         'can': 'cannot' }

    def test_process_stage_python_job(self):
        spec = { 'job': 'dumb',
                 'args': [1,2,3],
                 'stage': 'test',
                 'msg': 'wtf'}
        ret = self.bsg._process_stage(spec)
        expected = self.bsg.generate_job(spec, self.funcs)
        self.assertEqual(ret, expected)

    def test_process_stage_python_job_with_replacement(self):
        spec = { 'job': 'dumb',
                 'args': [1,2,3],
                 'stage': 'test',
                 'msg': 'wtf {can} this be or {is}'}

        ret = self.bsg._process_stage(spec, strings=self.strings)

        ex_spec = self.bsg.process_strings(spec, self.strings)
        expected = self.bsg.generate_job(ex_spec, self.funcs)

        self.assertEqual(ret, expected)

    def test_process_stage_shell_job(self):
        spec = { 'dir': '/tmp',
                 'args': [1,2,3],
                 'cmd': 'cat',
                 'stage': 'test',
                 'msg': 'wtf'}

        ret = self.bsg._process_stage(spec)
        expected = self.bsg.generate_shell_job(spec)
        self.assertEqual(ret, expected)

    def test_process_stage_shell_job_with_replacement(self):
        spec = { 'dir': '/tmp',
                 'args': [1,2,3],
                 'cmd': 'cat',
                 'stage': 'test',
                 'msg': 'wtf {can} this be or {is}'}

        ex_spec = self.bsg.process_strings(spec, self.strings)
        ret = self.bsg._process_stage(spec, strings=self.strings)
        expected = self.bsg.generate_shell_job(ex_spec)
        self.assertEqual(ret, expected)

    def test_process_stage_task_sequence(self):
        spec = { 'stage': 'test',
                 'tasks': [
                     { 'dir': '/tmp',
                       'args': [1,2,3],
                       'cmd': 'cat',
                       'stage': 'test',
                       'msg': 'wtf {can} this be or {is}'},
                     { 'job': 'dumb',
                       'args': [1,2,3],
                       'stage': 'test',
                       'msg': 'wtf' }
                    ],
                 'msg': 'wtf {can} this be or {is}'}

        ret = self.bsg._process_stage(spec)
        expected = (self.bsg.generate_sequence(spec, self.funcs).run, None)
        self.assertEqual(str(ret)[:-18], str(expected)[:-18])

    def test_process_stage_task_sequence_replacement(self):
        spec = { 'stage': 'test',
                 'tasks': [
                     { 'dir': '/tmp',
                       'args': [1,2,3],
                       'cmd': 'cat',
                       'stage': 'test',
                       'msg': 'wtf {can} this be or {is}'},
                     { 'job': 'dumb',
                       'args': [1,2,3],
                       'stage': 'test',
                       'msg': 'wtf' }
                    ],
                 'msg': 'wtf {can} this be or {is}'}

        ex_spec = self.bsg.process_strings(spec, self.strings)
        ret = self.bsg._process_stage(spec, strings=self.strings)
        expected = (self.bsg.generate_sequence(ex_spec, self.funcs).run, None)
        self.assertEqual(str(ret)[:-18], str(expected)[:-18])

    def test_invalid_spec(self):
        spec = { 'is': 'is not',
                 'can': 'cannot' }

        with self.assertRaises(InvalidJob):
            self.bsg._process_stage(spec)

    def test_invalid_spec_with_keys(self):
        spec_keys = set(['stage', 'task'])

        spec = { 'stage': 'is not',
                 'test': 'cannot',
                 'msg': 'stage' }

        with self.assertRaises(InvalidJob):
            self.bsg._process_stage(spec, spec_keys=spec_keys)

    def test_invalid_spec_with_keys(self):
        spec_keys = set(['stage', 'task'])

        spec = { 'is': 'is not',
                 'can': 'cannot' }

        with self.assertRaises(InvalidJob):
            self.bsg._process_stage(spec, spec_keys=spec_keys)

    def test_process_stage_shell_job_with_keys(self):
        spec_keys = set(['dir', 'cmd', 'args', 'stage'])

        spec = { 'dir': '/tmp',
                 'args': [1,2,3],
                 'cmd': 'cat',
                 'stage': 'test',
                 'msg': 'wtf'}

        ret = self.bsg._process_stage(spec)
        expected = self.bsg.generate_shell_job(spec)
        self.assertEqual(ret, expected)

class TestBuildSystemGenerator(TestCase):
    @classmethod
    def setUp(self):
        self.bsg = BuildSystemGenerator()

        self.funcs = { 'dumb': dummy_function,
                       'dump_new': dump_args_to_json_file_with_newlines,
                       'dump': dump_args_to_json_file }

    def test_initiation_funcs_empty(self):
        self.assertEqual(self.bsg.funcs, {})

    def test_initiation_funcs_initialized(self):
        func = { 'a': dummy_function }
        bs = BuildSystemGenerator(func)
        self.assertEqual(bs.funcs, func)

    def test_initiation_funcs_initialized_tuple(self):
        func = ('a', dummy_function)
        bs = BuildSystemGenerator(func)
        self.assertEqual(bs.funcs, {})

    def test_initiation_internal_stages(self):
        self.assertTrue(isinstance(self.bsg._stages, BuildSystem))

    def test_initiation_dependency_checking_object(self):
        self.assertTrue(isinstance(self.bsg.check, DependencyChecks))

    def test_initiation_empty_system(self):
        self.assertEqual(self.bsg.system, None)

    def test_initiation_of_tree_structures(self):
        self.assertTrue(isinstance(self.bsg._process_jobs, dict))
        self.assertTrue(isinstance(self.bsg._process_tree, dict))

    def test_initial_object_is_open(self):
        self.assertFalse(self.bsg._final)

    def test_check_method_correct_setting(self):
        self.assertEqual(self.bsg.check.check, self.bsg.check_method)

    def test_check_method_correct_value(self):
        self.assertTrue(self.bsg.check_method in self.bsg.check.checks)

    def test_check_method_resistance(self):
        o = self.bsg.check_method

        self.bsg.check_method = '_abcdefg'
        self.assertEqual(o, self.bsg.check_method)

    def test_check_method_change_success(self):
        o = self.bsg.check_method

        self.bsg.check_method = 'hash'
        self.assertNotEqual(o, self.bsg.check_method)

    def test_finalize_on_empty(self):
        with self.assertRaises(InvalidSystem):
            self.bsg.finalize()

    def test_finalize_second_time(self):
        self.bsg._final = True
        with self.assertRaises(InvalidSystem):
            self.bsg.finalize()

    ## TODO test job ordering in finalize()

    def test_process_strings_no_token(self):
        string = 'this string has no replacement tokens'
        self.assertEqual(self.bsg.process_strings(string, {}), string)

    def test_process_replacement_strings_not_dict(self):
        with self.assertRaises(TypeError):
            self.bsg.process_strings(['a'], 'f{o}o')

    def test_process_successful_replacement(self):
        new = 'this is not a car.'
        old = 'this {is} a car.'

        p = self.bsg.process_strings(old, { 'is': 'is not'})
        self.assertEqual(p, new)

    def test_process_irrelevant_spec(self):
        old = 'this {is} a car.'

        with self.assertRaises(InvalidJob):
            p = self.bsg.process_strings(old,{ "isn't'": 'is not'})

    def test_process_half_relevant_spec(self):
        old = 'this {works} or {not}'
        new = 'this wwworks or {not}'
        strings = {'works': 'wwworks', 'car': 'cccar'}

        with self.assertRaises(InvalidJob):
            self.assertEqual(self.bsg.process_strings(old, strings), new)

    def test_process_replacements_in_dict(self):
        old = {'message': 'this {car} {works}'}
        new = {'message': 'this cccar wwworks'}
        strings = {'works': 'wwworks', 'car': 'cccar'}

        ret = self.bsg.process_strings(old, strings)
        self.assertEqual(ret, new)

        alt = { 'message': old['message'].format(**strings)}
        self.assertEqual(alt, new)

    def test_generate_job_list(self):
        args = (1, 2)
        expected = (dummy_function, args)
        ret = self.bsg.generate_job({'job': 'dumb', 'args': [1, 2]}, self.funcs)

        self.assertEqual(expected, ret)

    def test_generate_job_tuple(self):
        args = (1, 2)
        expected = (dummy_function, args)
        ret = self.bsg.generate_job({'job': 'dumb', 'args': args}, self.funcs)

        self.assertEqual(expected, ret)

    def test_generate_job_dict(self):
        args = {'a': 1, 'b': 2}
        expected = (dummy_function, args)
        ret = self.bsg.generate_job({'job': 'dumb', 'args': args}, self.funcs)

        self.assertEqual(expected, ret)

    def test_generate_job_malformed_args(self):
        args = BuildSystem()

        with self.assertRaises(InvalidJob):
            self.bsg.generate_job({'job': 'dumb', 'args': args}, self.funcs)

    def test_generate_job_non_extant_function(self):
        args = (1, 2)

        with self.assertRaises(InvalidJob):
            self.bsg.generate_job({'job': 'Nope', 'args': args}, self.funcs)

    def test_generate_job_list_func_callable(self):
        args = (1, 2)
        expected = (dummy_function, args)
        ret = self.bsg.generate_job({'job': dummy_function, 'args': [1, 2]}, self.funcs)

        self.assertEqual(expected, ret)

    def test_generate_job_tuple_func_callable(self):
        args = (1, 2)
        expected = (dummy_function, args)
        ret = self.bsg.generate_job({'job': dummy_function, 'args': args}, self.funcs)

        self.assertEqual(expected, ret)

    def test_generate_job_dict_func_callable(self):
        args = {'a': 1, 'b': 2}
        expected = (dummy_function, args)
        ret = self.bsg.generate_job({'job': dummy_function, 'args': args}, self.funcs)

        self.assertEqual(expected, ret)

    def test_generate_job_malformed_args_func_callable(self):
        args = BuildSystem()

        with self.assertRaises(InvalidJob):
            self.bsg.generate_job({'job': dummy_function, 'args': args}, self.funcs)

    def test_adding_task_to_funcs(self):
        self.assertEqual(self.bsg.funcs, {})
        self.bsg.add_task('foo', dummy_function)
        self.assertEqual(self.bsg.funcs, {'foo': dummy_function})

    def test_adding_task_to_funcs_invalid_job(self):
        self.assertEqual(self.bsg.funcs, {})
        with self.assertRaises(InvalidJob):
            self.bsg.add_task('foo', BuildSystemGenerator)
        self.assertEqual(self.bsg.funcs, {})

    # TODO tests for ingest_yaml
    # TODO tests for ingest_json

    def test_dependency_string_full_name(self):
        spec = { 'dependency': 'a b c d',
                 'target': '/tmp/files',
                 'msg': 'alpha' }
        expected = [ 'a', 'b', 'c', 'd' ]

        self.assertEqual(self.bsg.get_dependency_list(spec), expected)

    def test_dependency_string_shortest(self):
        spec = { 'dep': 'a b c d',
                 'target': '/tmp/files',
                 'msg': 'alpha' }
        expected = [ 'a', 'b', 'c', 'd' ]

        self.assertEqual(self.bsg.get_dependency_list(spec), expected)

    def test_dependency_string_short_alt(self):
        spec = { 'deps': 'a b c d',
                 'target': '/tmp/files',
                 'msg': 'alpha' }
        expected = [ 'a', 'b', 'c', 'd' ]

        self.assertEqual(self.bsg.get_dependency_list(spec), expected)

    def test_dependency_list_full_name(self):
        spec = { 'dependency': ['a', 'b', 'c', 'd'],
                 'target': '/tmp/files',
                 'msg': 'alpha' }
        expected = [ 'a', 'b', 'c', 'd' ]

        self.assertEqual(self.bsg.get_dependency_list(spec), expected)

    def test_dependency_list_shortest(self):
        spec = { 'dep': ['a', 'b', 'c', 'd'],
                 'target': '/tmp/files',
                 'msg': 'alpha' }
        expected = [ 'a', 'b', 'c', 'd' ]

        self.assertEqual(self.bsg.get_dependency_list(spec), expected)

    def test_dependency_list_short_alt(self):
        spec = { 'deps': ['a', 'b', 'c', 'd'],
                 'target': '/tmp/files',
                 'msg': 'alpha' }
        expected = [ 'a', 'b', 'c', 'd' ]

        self.assertEqual(self.bsg.get_dependency_list(spec), expected)

    def test_process_job_with_stage_and_target(self):
        spec = {
            'target': 'other',
            'dependency': 'string',
            'job': 'dumb',
            'args': None,
            'stage': 'one',
        }

        with self.assertRaises(InvalidJob):
            self.bsg._process_job(spec)


    def test_process_dependency(self):
        self.bsg.check.check = 'force'
        spec = { 'deps': ['a', 'b', 'c', 'd'],
                 'target': '/tmp/files',
                 'msg': 'alpha' }

