# Copyright 2013 Sam Kleinman
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

"""
:mod:`system` is an interface for specifying and executing a build process with
concurrent semantics. It provides abstractions for running build processes that
are :class:`~stages.BuildSequence()` and :class:`~stages.BuildStage()` objects.

:class:`~system.BuildSystemGenerator()` uses the tools in :mod:`stages` to
produce a build system and provide the foundation of the command-line build
system tool :ref:`buildc`.
"""

import json
import logging

from buildcloth.err import InvalidStage, StageClosed, StageRunError, InvalidJob, InvalidSystem
from buildcloth.tsort import topological_sort
from buildcloth.stages import BuildSequence, BuildStage, BuildSteps
from buildcloth.dependency import DependencyChecks
from buildcloth.utils import is_function

logger = logging.getLogger(__name__)

try:
    import yaml
except ImportError:
    pass

class BuildSystem(object):
    """
    A representation of a multi-stage build system that combines a number build
    stages to be constructed in any order, and executed sequentially.
    """

    def __init__(self, initial_system=None):
        """
        :param BuildSystem initial_system: A :class:~system.BuildSystem` object
           that define a series of build steps.
        """

        self._stages = []
        "An internal representation of order of the stages."

        self.stages = {}
        "A mapping of the names of stages to their stage objects."

        self.open = True
        """Boolean. If ``True``, (and ``strict`` is ``True``,)then it's safe to
        add additional stages and execute the build"""

        self._strict = True
        """Boolean. Internal strictness mode. Defaults to ``True``. When
        ``False`` makes it possible to add stages to a finalized build or run
        un-finalized build processes"""

        if initial_system is not None:
            logger.debug('creating BuildSystem object with a default set of stages.')
            self.extend(initial_system)

        logger.info('created BuildSystem object.')

    @property
    def closed(self):
        """
        :returns: ``True`` when after finalizing a :class:~system.BuildSystem`
           object.
        """
        return not self.open

    @property
    def strict(self):
        """
        A Getter and setter for the :attr:~system.BuildSystem._strict` setting.
        """
        return self._strict

    @strict.setter
    def strict(self, value):
        logger.info('changing default object strictness setting.')
        self._strict = value

    def close(self):
        "Sets the :attr:`~system.BuildSystem.open` value to ``False``."
        if self.open is True:
            logger.info('closing BuildSystem with stages: {0}'.format(self._stages))
            self.open = False

    def _validate_stage(self, name):
        """
        :param string name: The name of a stage.

        :returns: ``False`` when ``name`` already exists in the build system,
           and ``True`` otherwise.
        """

        if name in self.stages:
            return False
        else:
            return True

    def new_stage(self, name):
        """
        :param string name: The name of a stage.

        Special case and wrapper of :meth:~system.BuildSystem.add_stage()` that
        adds a new stage without adding any jobs to that stage.
        """

        logger.info('creating a new stage named {0}'.format(name))
        self.add_stage(name, stage=None)

    def extend(self, system):
        """
        :param BuildSystem system: A :class:`~system.BuildSystem()` object.

        Takes ``system`` and grows the current :class:`~system.BuildSystem()`
        object to have the objects stages. If there are existing stages and job
        definitions that collide with stages and jobs in ``system``, the data in
        ``system`` wins.
        """

        self.stages.update(system.stages)

        for job in system._stages:
            self._stages.append(job)
            logger.debug('extending system with: {0}'.format(job))

    def add_stage(self, name, stage=None, stage_type=None, strict=None):
        """
        :param string name: The name of a stage.

        :param BuildStage stage: A :class:~stages.BuildSteps` object. Default's
           to ``None``, which has the same effect as
           :meth:~system.BuildSystem.new_stage()`.

        :param string stage_type: Either ``sequence`` (or ``seq``) or ``stage``
           to determine what kind of :class`~stages.BuildSteps()` object to
           instantiate if ``stage`` is ``None``

        :param bool strict: Overrides the default
           :attr:`~system.BuildSystem.strict` attribute. When ``True``, prevents
           callers from adding duplicate stages to a :class:~system.BuildSystem`
           object.

        :raises: :err:`~err.InvalidStage()` in strict mode if ``name`` or
           ``stage`` is malformed.

        Creates a new stage and optionally populates the stage with tasks. Note
        the following behaviors:

        - If ``name`` exists in the current :class:~system.BuildSystem`,
          ``strict`` is ``False``, and ``stage`` is ``None``; then
          :meth:~system.BuildSystem.add_stage()` adds the stage with ``name`` to
          the current :class:~system.BuildSystem` object. This allows you to
          perform the same stage multiple times in one build process.

        - If ```name`` does not exist in the current
          :class:~system.BuildSystem`, and ``stage`` is ``None``,
          :meth:~system.BuildSystem.add_stage()` adds the stage and instantiates
          a new :class`~stages.BuildSteps()` (either
          :class`~stages.BuildSequence()` or :class`~stages.BuildStage()`
          depending on the value of ``stage_type``) object with ``name`` to the
          current :class:~system.BuildSystem` object.

          :meth:~system.BuildSystem.add_stage()` must specify a ``stage_type``
          if ``stage`` is ``None``. When ``strict`` is ``True`` not doing so
          raises an exception.

        - Adds the ``stage`` with the specified :class`~stages.BuildSteps()`
          object to the :class:~system.BuildSystem` object. Raises an exception
          if ``stage`` is not a :class`~stages.BuildSteps()` object.
        """

        if strict is None:
            logger.info('defaulting to default object strictness value {0}'.format(self.strict))
            strict = self.strict
        else:
            logger.info('strict value currently: {0}'.format(strict))

        # add duplicate item to stage if: not strict, it already exists, and
        # stage arg is none:
        if self._validate_stage(name) is False:
            if not strict:
                if stage is None:
                    self._stages.append(name)
                    logger.debug('added duplicate stage named {0}'.format(name))
                else:
                    logger.critical('exception: stage name {0} already exists'.format(name))
                    raise InvalidStage("can't add duplicate stages with new jobs'")
        else: # stage does not already exist
            logger.debug('stage name {0} does not exist, continuing'.format(name))
            if stage is None and stage_type is None:
                logger.warning('stage {0} is empty no type is specified.'.format(name))
                # error case, stages must have a type
                if strict is True:
                    logger.critical('in strict mode, raising exception.')
                    raise InvalidStage("New stages must have a type")
                elif strict is False:
                    logger.warning('in permissive mode; aborting, returning early.')
                    return False
            elif stage is None and stage_type is not None:
                # add blanks if needed
                logger.info('adding a blank stage named "{0}"'.format(name))
                if stage_type.startswith('seq'):
                    logger.debug('adding a build sequence stage.')
                    stage = BuildSequence()
                elif stage_type.startswith('stage'):
                    stage = BuildStage()
                    logger.debug('adding a parallel build stage stage.')
                else:
                    logger.critical('no stage type available named {0}'.format(stage_type))
                    if strict is True:
                        logger.critical('in strict mode, raising exception.')
                        raise InvalidStage("New stages must have a type")
                    else:
                        logger.warning('in permissive mode; aborting, returning early.')
                        return False
            else:
                # add stage as specified.
                if isinstance(stage, BuildSteps) is False:
                    logger.critical('{0} is not a build step object'.format(name))
                    if strict is True:
                        logger.critical('in strict mode, raising exception.')
                        raise InvalidStage("must add a BuildSteps object to a build system.")
                    else:
                        logger.warning('in permissive mode; aborting, returning early.')
                        return False

                # if we get here it's safe to add things
                logger.info('appending well formed stage.')
                self._stages.append(name)
                self.stages[name] = stage

                return True

    def get_order(self):
        """
        :returns: List of names of build stages in the order they'd run.
        """
        return self._stages

    def get_stage_index(self, stage):
        """
        :param string stage: The name of a stage in the
           :class:`~system.BuildSystem`.

        :returns: The position of the stage in the :class:`~system.BuildSystem`,
           or ``None`` if it doesn't exist in the :class:`~system.BuildSystem`
           object.
        """

        if stage in self._stages:
            return self._stages.index(stage)
        else:
            return None

    def count(self):
        """
        :returns: The number of stages in the :class:~system.BuildSystem` object.
        """
        return len(self._stages)

    def stage_exists(self, name):
        """
        :param string name: The name of a possible stage in the
           :class:~system.BuildSystem` object.

        :returns: ``True`` if the stage exists in :class:~system.BuildSystem`
           and ``False`` otherwise.
        """

        if name in self._stage:
            return True
        else:
            return False

    def run_stage(self, name, strict=None):
        """
        :param string name: The potential name of a stage in the
           :class:~system.BuildSystem` object.

        :param bool strict: Defaults to :attr:`~system.BuildSystem.strict`.

        :returns: ``False`` if ``name`` is not in the
           :class:~system.BuildSystem` object, and ``strict`` is
           ``False``. In all other cases
           :meth:`~system.BuildSystem.run_stages()` returns ``True`` after the
           stage runs.

        :raises: :exc:`~err.StageRunError` if ``strict`` is ``True`` and
           ``name`` does not exist.

        Runs a single stage from the :class:~system.BuildSystem` object.
        """
        if strict is None:
            strict = self.strict

        if name not in self.stages:
            if strict is True:
                raise StageRunError("Stage must exist to run.")
            else:
                return False
        else:
            self.stages[name].run(strict)
            return True

    def run_part(self, idx, strict=None):
        """
        :param int idx: The zero-indexed identifier of the stage.

        :param bool strict: Defaults to :attr:`~system.BuildSystem.strict`.

        :raises: :exc:`~err.StageRunError` if ``strict`` is ``True`` and
           :attr:`~system.BuildSystem.open` is ``True``.

        Calls the :meth:`~stages.BuildSteps.run()` method of each stage object
        until the ``idx``\ :sup:`th` item of the.
        """

        if strict is None:
            logger.debug('defaulting to object default strict mode.')
            strict = self.strict

        if strict is True and self.open is True:
            logger.critical('cannot run build systems that are open in strict mode.')
            raise StageRunError("Build system must be closed before running.")
        else:
            for job in self._stages[:idx]:
                logger.info('running build stage {0}'.format(job))
                self.stages[job].run()
                logger.info('completed build stage {0}'.format(job))

    def run(self, strict=None):
        """
        :param bool strict: Defaults to :attr:`~system.BuildSystem.strict`.

        :raises: :exc:`~err.StageRunError` if ``strict`` is ``True`` and
           :attr:`~system.BuildSystem.open` is ``True``.

        Calls the :meth:`~stages.BuildSteps.run()` method of each stage object.
        """
        logger.info('running entire build system')
        self.run_part(idx=self.count() - 1, strict=strict)

class BuildSystemGenerator(object):
    """
    :class:`~system.BuildSystemGenerator` objects provide a unifying interface
    for generating and running :class:`~system.BuildSystem` objects from
    easy-to-edit sources. :class:`~system.BuildSystemGenerator` is the
    fundamental basis of the :ref:`buildc` tool.

    :param dict funcs: Optional. A dictionary that maps callable objects
       (values), to identifiers used by build system definitions. If you do not
       specify.

    :class:`~system.BuildSystemGenerator` is designed to parse streams of YAML
    documents that resemble the following:

    .. code-lock:: yaml

       job: <func>
       args: <<arg>,<list>>
       stage: <str>
       ---
       job: <func>
       args: <<arg>,<list>>
       target: <str>
       dependency: <<str>,<list>>
       ---
       dir: <<path>,<list>>
       cmd: <str>
       args: <<arg>,<list>>
       stage: <str>
       ---
       dir: <<path>,<list>>
       cmd: <str>
       args: <<arg>,<list>>
       dependency: <<str>,<list>>
       ---
       tasks:
         - job: <func>
           args: <<arg>,<list>>
         - dir: <<path>,<list>>
           cmd: <str>
           args <<args>,<list>>
       stage: <str>
       ...

    See :ref:`build-stages` for complete documentation of the input data format
    and its use.
    """

    def __init__(self, funcs=None):
        if isinstance(funcs, dict):
            self.funcs = funcs
            logger.info('created build generator object with a default job mapping.')
        else:
            self.funcs = {}
            logger.info('created build generator object with an empty job mapping.')

        self._stages = BuildSystem()
        logger.info('created empty build system object for build generator.')

        self._process_jobs = {}
        "Mapping of targets to job tuples."

        self._process_tree = {}
        "Internal representation of the dependency tree."

        self.system = None

        self._final = False
        """Internal switch that indicates a finalized method. See
        :meth:`~system.BuildSystemGenerator.finlize()` for more information."""

        self.check = DependencyChecks()

        logger.info('created build system generator object')

    @property
    def check_method(self):
        return self.check.check

    @check_method.setter
    def check_method(self, value):
        if value not in self.check.checks:
            pass
        else:
            self.check.check = value

    def finalize(self):
        """
        :raises: :exc:`~err.InvalidSystem` if you call
           :meth:`~system.BuildSystemGenerator.finalize()` more than once on a
           single :class:`~system.BuildSystemGenerator()` object.

        You must call :meth:`~system.BuildSystemGenerator.finalize()` before
        running the build system.

        :meth:`~system.BuildSystemGenerator.finalize()` compiles the build
        system. If there are no tasks with dependencies,
        :attr:`~system.BuildSystemGenerator._stages` becomes the
        :attr:`~system.BuildSystemGenerator.system` object. Otherwise,
        :meth:`~system.BuildSystemGenerator.finalize()` orders the tasks with
        dependencies, inserts them into a :class:`~stages.BuildSequence` object
        before inserting the :attr:`~system.BuildSystemGenerator._stages` tasks.
        """

        if self._final is False and self.system is None:

            if len(self._process_tree) == 0:
                logger.debug('no dependency tasks exist, trying to add build stages.')
                if self._stages.count() > 0:
                    self.system = self._stages
                    logger.info('added tasks from build stages to build system.')
                else:
                    logger.critical('cannot finalize empty generated BuildSystem object.')
                    raise InvalidSystem

            elif len(self._process_tree) > 0:
                self.system = BuildSystem()

                self._process = topological_sort(self._process_tree)
                logger.debug('successfully sorted dependency tree.')

                rebuilds_needed = False
                for i in self._process:
                    if rebuilds_needed is False and self._process_jobs[i][1] is True:
                        logger.deug('{0}: needs rebuild.'.format(i))
                        rebuilds_needed = True
                    else:
                        logger.debug('{0}: does not need a rebuild, passing'.format(i))
                        continue

                    if rebuilds_needed is True:
                        logger.debug('{0}: adding to rebuild queue'.format(i))
                        self.system.add_stage(i, self._process_jobs[i][0][0], self._process_jobs[i][0][1])

                if self._stages.count() > 0:
                    self.system.extend(self._stages)
                    logger.info('added stages tasks to build system.')

            self.system.close()

        else:
            logger.critical('cannot finalize object')
            raise InvalidBuildSystem

    @staticmethod
    def process_strings(spec, strings):
        if not strings:
            return spec
        else:
            for k, v  in spec.items():
                if '{' in v:
                    spec[k] = v.format(strings)

            return spec

    @staticmethod
    def generate_job(spec, funcs):
        """
        :param dict spec: A *job* specification.

        :param dict funcs: A dictionary mapping names (i.e. ``spec.job`` to
            functions.)

        :returns: A tuple where the first item is a callable and the second item
           is either a dict or a tuple of arguments, depending on the type of
           the ``spec.args`` value.

        :raises: :exc:`~err.InvalidStage` if ``spec.args`` is neither a
           ``dict``, ``list``, or ``tuple``.
        """

        if isinstance(spec['args'], dict):
            args = spec['args']
        elif isinstance(spec['args'], list):
            args = tuple(spec['args'])
        elif isisntance(spec['args'], tuple):
            args = spec['args']
        else:
            raise InvalidStage('args are malformed.')

        return funcs[spec['job']], args

    @staticmethod
    def generate_shell_job(spec):
        """
        :param dict spec: A *job* specification.

        :returns: A tuple where the first element is :mod:`python:subprocess`
           :func:`~python:subprocess.call`, and the second item is a dict
           ``args``, a ``dir``, and ``cmd`` keys.

        Takes a ``spec`` dict and returns a tuple to define a task.
        """

        import subprocess

        if isinstance(spec['cmd'], list):
            cmd_str = spec['cmd']
        else:
            cmd_str = spec['cmd'].split()

        if isinstance(spec['dir'], list):
            spec['dir'] = os.path.sep.join(spec['dir'])

        if isinstance(spec['args'], list):
            cmd_str.extend(spec['args'])
        else:
            cmd_str.extend(spec['args'].split())

        return subprocess.call, dict(cwd=spec['dir'],
                                     args=cmd_str)

    @staticmethod
    def generate_sequence(spec, funcs):
        """
        :param dict spec: A *job* specification.

        :param dict funcs: A dictionary mapping names to callable objects.

        :returns: A :class:`~stages.BuildSequence()` object.

        :raises: An exception when ``spec`` does not have a ``task`` element or
           when ``task.spec`` is not a list.

        Process a job spec that describes a sequence of tasks and returns a
        :class:`~stages.BuildSequence()` object for inclusion in a
        :class:`~system.BuildSystem()` object.
        """

        sequence = BuildSequence()

        if 'task' not in spec and not isinstance(task['spec'], list):
            raise InvalidStage
        else:
            for task in spec['tasks']:
                if 'job' in task:
                    job, args = _generate_yaml_build_job(task, funcs)
                elif 'cmd' in task:
                    job, args = _generate_shell_build_job(task)

                sequence.add(job, args)

                sequence.close()

            return sequence

    def add_task(self, name, func):
        """
        :param string name: The identifier of a callable.

        :param callable func: A callable object.

        :raises: :exec:`~err.InvaidJob` if ``func`` is not callable.

        Adds a callable object to the :attr:`~system.BuildSystemGenerator.funcs`
        attribute with the identifier ``name``.
        """
        if not is_function(func):
            logger.critical('cannot add tasks that are not callables ({0}).'.format(name))
            raise InvalidJob("{0} is not callable.".format(func))

        logger.debug('adding task named {0}'.format(name))
        self.func[name] = func

    def ingest_yaml(self, filename, strings=None):
        """
        :param string filename: The fully qualified path name of a :term:`YAML`
           file that contains a build system specification.

        :param dict strings: Optional. A dictionary of strings mapping to
           strings to use as replacement keys for spec content.

        For every document in the YAML file specified by ``filename``, calls
        :meth:`~system.BuildSystemGenerator._process_job()` to add that job to
        the :attr:`~system.BuildSystemGenerator.system` object.
        """

        logger.debug('opening yaml file {0}'.format(filename))
        try:
            with open(filename, 'r') as f:
                try:
                    jobs = yaml.safe_load_all(f)
                except NameError:
                    msg = 'attempting to load a yaml definition without PyYAML installed.'
                    logger.critical(msg)
                    raise StageRunError(msg)

                job_count = 0
                for spec in jobs:
                    self._process_job(spec, strings)
                    job_count += 1

            logger.debug('loaded {0} jobs from {1}'.format(job_count, filename))
        except IOError:
            logger.warning('file {0} does not exist'.format(filename))

    def ingest_json(self, filename, strings=None):
        """
        :param string filename: The fully qualified path name of a :term:`JSON`
           file that contains a build system specification.

        :param dict strings: Optional. A dictionary of strings mapping to
           strings to use as replacement keys for spec content.

        For every document in the JSON file specified by ``filename``, calls
        :meth:`~system.BuildSystemGenerator._process_job()` to add that job to
        the :attr:`~system.BuildSystemGenerator.system` object.
        """

        logger.debug('opening json file {0}'.format(filename))
        try:
            with open(filename, 'r') as f:
                jobs = json.load(f)

                for spec in jobs:
                    self._process_job(spec, strings)

            logger.debug('loaded {0} jobs from {1}'.format(job_count, filename))
        except IOError:
            logger.warning('file {0} does not exist'.format(filename))

    def _process_stage(self, spec, spec_keys, strings=None):
        """
        :param dict spec: The task specification imported from user input.

        :param set spec_keys: A set containing the top level keys in the set.

        :param dict strings: Optional. A dictionary of strings mapping to
           strings to use as replacement keys for spec content.

        :returns: A two item tuple, containing a function and a list of arguments.

        :raises: :exc:`~err.InvalidJob` if the schema of ``spec`` is not recognized.

        Based on the schema of the ``spec``, creates tasks and sequences to add
        to a BuildSystem using, as appropriate one of the following methods:

        - :meth:`~system.BuildSystemGenerator.generate_job()`,
        - :meth:`~system.BuildSystemGenerator.generate_shell_job()`, or
        - :meth:`~system.BuildSystemGenerator.generate_sequence()`.
        """

        spec_keys = set(spec.keys())

        if self.funcs and spec_keys.issuperset(set('job', 'args', 'stage')):
            logger.debug('spec looks like a pure python job, processing now.')
            spec = self.process_strings(spec, strings)
            return self.generate_job(spec, self.funcs)
        elif spec_keys.issuperset(set('dir', 'cmd', 'args', 'stage')):
            logger.debug('spec looks like a shell job, processing now.')
            spec = self.process_strings(spec, strings)
            return self.generate_shell_job(spec)
        elif self.funcs and spec_keys.issuperset(set('stage', 'tasks')):
            logger.debug('spec looks like a shell job, processing now.')
            spec = self.process_strings(spec, strings)
            task_sequence = self.generate_sequence(spec, self.funcs)
            return task_sequence.run, None
        else:
            logger.critical('spec does not match existing job type, returning early')
            raise InvalidJob

    @staticmethod
    def get_dependency_list(spec):
        """
        :param dict spec: A specification of a build task with a ``target``, to process.

        :returns: A list that specifies all specified dependencies of that task.
        """

        try:
            dependency = spec['dep']
        except KeyError:
            dependency = spec['dependency']
        except KeyError:
            dependency = spec['deps']
        else:
            logger.warning('no dependency in {0} spec'.format(spec['target']))
            return list()

        if isinstance(dependency, list):
            return dependency
        else:
            return dependency.split()

    def _process_dependency(self, spec):
        """
        :param dict spec: The task specification imported from user input.

        Wraps :meth:`~system.BuildSystemGenerator._process_stage()` and
        additionally modifies the internal strucutres associated with the
        dependency tree.
        """

        job = _process_stage(spec)
        dependencies = self.get_dependency_list(spec)

        if self.check.check(spec['target'], dependencies) is True:
            msg = 'target {0} is older than dependency {1}: adding to build queue'
            logger.info(msg.format(spec['target'], dependencies))

            self._process_jobs[spec['target']] = (job, True)
        else:
            logger.info('rebuild not needed for {0}.')
            self._process_jobs[spec['target']] = (job, False)

        logger.debug('added {0} to dependency graph'.format(spec['target']))
        self._process_tree[spec['target']] = self.get_dependency_list(spec)


    def _process_job(self, spec):
        """
        :param dict spec: A dictionary of strings that describe a build job.

        Processes the ``spec`` and attempts to create and add the resulting task
        to the build system.
        """

        # make sure there's a dependency
        if 'target' in spec:
            if 'dep' not in spec or 'dependency' not in spec:
                # put this into the BuildSystem stage to run after the dependency tree.
                spec['stage'] = '__nodep'

                msg = 'adding task with target: {0} to final build stage since no dependency specified.'
                logger.info(msg.format(spec['target']))

                # to avoid confusion:
                logger.debug('removing target key from spec: {0}'.format(spec['target']))
                del spec['target']
            else:
                _process_dependency(spec)
                logger.debug('added task to build {0}'.foramt(spec['target']))
                return True

        if 'stage' not in spec:
            logger.warning('job lacks stage name, adding one to "{1}", please correct.'.format(spec))
            spec['stage'] = '__unspecified'

        job = _process_stage(spec)

        if not self.system.stage_exists(spec['stage']):
            logger.debug('creating new stage named {0}'.format(spec['stage']))
            self.system.new_stage(spec['stage'])

        self._stages.stages[spec['stage']].add(job[0], job[s1])
        logger.debug('added job to stage: {0}'.format(spec['stage']))
