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
:mod:`stages` is a complete build system tool that provides an interface for
specifying and executing a build process with concurrent semantics.

Tasks (i.e. functions) are the smallest unit of work, and are typically Python
functions, although a task may be shell commands in some cases. :mod:`stages`
allows you to specify three basic relationships between tasks:

*Sequence*
   A series of tasks which must be executed in a specific order. Provided by
   :class:`~stages.BuildSequence()`.

   A group of tasks that can be executed in any order, and potentially
   concurrently. Provided by :class:`~stages.BuildStage()`.

*System*
   The collection of *sequences* and *stages*.

:class:`~stages.BuildSequence()` and :class:`~stages.BuildStage()` share the
same base class (:class:`~stages.BuildSteps()`) and have a common interface
despite different behaviors.

Finally, :class:`~stages.BuildSystemGenerator()` uses the other tools in
:mod:`stages` to produce a build system and provide the foundation of the
command-line build system tool :ref:`buildc`.
"""

from multiprocessing import cpu_count, Pool
import types
import json
import logging

from buildcloth.err import InvalidStage, StageClosed, StageRunError, InvalidJob, InvalidSystem
from buildcloth.tsort import topological_sort

logger = logging.getLogger(__name__)

try:
    import yaml
except ImportError:
    pass

class BuildSteps(object):
    """
    :param BuildStage initial_stage:

       Optional. You may optionally pass a :class:`~stages.BuildSequence()` or
       :class:`~stages.BuildStage()` object to
       :class:`~stages.BuildSteps()`. Otherwise, the new object will initialize
       an empty task list.

    :class:`~stages.BuildSteps()` is an object that stores a representation of a
    group of tasks. In practice, :class:`~stages.BuildSteps()` is the base class
    for specific implementations for groups of build tasks. In practice
    sub-classes simply implement the :meth:`~stages.BuildSteps.run()` method
    which raises a :exc:`python:NotImplementedError`.
    """

    def __init__(self, initial_stage=None):
        logger.info('creating a BuildSteps object directly.')

        self.stage = []
        """A list of task objects. See :meth:`~stages.BuildSteps.add()` for
        information on the form of a task."""

        self._open = True
        """A boolean, that when ``False`` 'closes' the
        :class:`~stages.BuildSteps()` object and prevents callers from adding
        additional tasks."""

        self._workers = cpu_count
        """An attribute that specifies the number of worker processes used in
        the pool for builds run in parallel."""

        if initial_stage is not None:
            self.add(initial_stage)

        logger.info('created a BuildStep object.')

    @property
    def closed(self):
        """Is ``True`` if the :class:`~stages.BuildSteps()` is mutable, and
        ``False`` otherwise."""

        return not self._open

    def close(self):
        """If :class:`~stages.BuildSteps()` is mutable, finalizes the object to
        prevent further editing. Returns ``False`` to reflect the current
        mutability state of the object."""

        if self._open is True:
            self._open = False
            logger.info('closed object object.')
        else:
            logger.debug('called close() on already closed BuildSteps object.')

        return self._open

    @property
    def workers(self):
        """The size of the worker pool that will process the tasks in this group
        or stage of tasks. Set ``workers`` to the number of jobs you want to
        execute in parallel. By default this is the number of cores/threads
        available on your system.

        The minimum value for :meth:`~stages.BuildSteps.workers` is ``2``, and
        cannot be set to a value lower than ``2``."""

        return self._workers

    @workers.setter
    def workers(self, value):
        if value <= 1:
            self._workers = 2
            logger.debug("worker values must be at least 2, cannot have a pool with {0} loggers".format(value))
        else:
            self._workers = value
            logger.debug("set the default size of the worker pool to {0}".format(value))

    @staticmethod
    def validate(stage, strict=False):
        """
        :param iterable stage: A stage object to validate.

        :param bool strict: Defaults to ``False``. When ``True``,
           :meth:`~stages.BuildSteps.validate()` raises exceptions when it
           detects an invalid object. Otherwise,
           :meth:`~stages.BuildSteps.validate()` returns ``False`` for invalid
           stage objects and ``True`` for valid stage objects

        :raises: :exc:`~err.InvalidStage` in strict-mode.

        Used internally to ensure that stage objects are well formed before
        inserting them into the build :class:~stages.BuildSteps` object.
        """

        if len(stage) < 2:
            logger.critical('the stage object is malformed and has too few elements.')

            if strict:
                logger.warning('strict mode, error causing an exception.')
                raise InvalidStage('malformed stage')
            else:
                logger.warning('in permissive mode, error  returning false.')
                return False

        if not isinstance(stage[0],(types.BuiltinFunctionType,
                                    types.FunctionType,
                                    types.MethodType)):
            logger.critical('the  in the stage is not callable.')

            if strict:
                logger.warning('strict mode, error causing an exception.')
                raise InvalidStage('not a callable')
            else:
                logger.warning('in permissive mode, error  returning false.')
                return False

        if not isinstance(stage[1], tuple) and not isinstance(stage[1], dict) and not isinstance(stage[1], list):
            if strict:
                logger.warning('strict mode, error causing an exception.')
                raise InvalidStage('not a tuple or dict')
            else:
                logger.warning('in permissive mode, error  returning false.')
                return False

        return True

    def add(self, func, args, strict=True):
        """
        :param callable func: A callable object (e.g. function or method) to run
            as a job.

        :param tuple args: A tuple or dict of arguments to pass to the callable.

        :param bool strict: Defaults to ``True``. When ``True``, raises
            exceptions when attempting to perform inadmissible actions. If
            strict is ``False``, will continue to operate silently.

        :raises: :exc:`err.StageClosed` in strict mode, if attempting to add to
            an already closed stage.

        Adds a job to a :class:~stages.BuildSteps` object. If ``strict`` is
        ``True``, :meth:~stages.BuildSteps.add()` raises exceptions if you
        attempt to add a task to a non-open :class:~stages.BuildSteps` object or
        add a malformed job to the :class:~stages.BuildSteps` object.
        """

        if self._open is False:
            if strict is True:
                logger.warning('strict mode, error causing an exception.')
                raise StageClosed('cannot add to closed stage.')
            else:
                logger.warning('in permissive mode, error  returning false.')
                return False

        stage = (func, args)
        if self.validate(stage, strict):
            self.stage.append(stage)
            logger.info('added stage calling {0}'.format(func.__name__))
            return True
        else:
            logger.critical('did not add object with "{0}" to object because it did not validate'.format(func))
            if strict is True:
                raise InvalidStage('cannot add invalid object.')
            else:
                return False

    def extend(self, jobs, strict=True):
        """
        :param list jobs: A list of job specifications, or tuples where the
           first item is a callable and the second item is a tuple or dict of
           arguments.

        :param bool strict: Toggles strict mode for :meth:~stages.BuildSteps.add()`.

        A wrapper around :meth:~stages.BuildSteps.add()` for adding multiple
        jobs to a :class:~stages.BuildSteps` object. To add jobs from one
        :class:~stages.BuildSteps` object to another, use the following
        operation:

        .. code-block:: python

           seq = BuildStage()
           st = BuildStage()
           seq.add(func, args)
           st.extend(seq.stage, strict=False)
        """
        logger.info("adding a group of jobs to stage.")

        for func, args in jobs:
            self.add(func, args, strict)

        logger.info("completed adding group to stage.")

    def grow(self, func, arg_list, strict=True):
        """
        :param callable func: A callable oject (e.g. function or method) to run
           as a job.

        :param list arg_list: A list of tuples, which are arguments to ``func``
            for a sequence of jobs.

        :param bool strict: Toggles strict mode for :meth:~stages.BuildSteps.add()`.

        Use to add a sequence of jobs to a :class:~stages.BuildSteps` object
        that use the same ``func`` but different arguments.
        """

        try:
            logger.info('adding group of {0} operations to build stage'.format(func.__name__))
        except AttributeError:
            logger.warning('attempting to add a group of tasks with an odd callable')

        for arg in arg_list:
            self.add(func, arg, strict)

    def count(self):
        """
        :returns: The number of items in the :class:~stages.BuildSteps` object.
        """
        return len(self.stage)

    def run(self):
        """
        :raises: :exc:`python:NotImplementedError()`
        """
        raise NotImplementedError

class BuildStage(BuildSteps):
    """
    A subclass of :class:~stages.BuildSteps` that executes jobs using a
    :mod:`python:multiprocessing` worker pool.
    """

    def run(self, workers=None):
        """
        :param int workers: Overrides the :meth:~stages.BuildSteps.workers`
           value, which is typically the number of CPU cores your system has.

        Runs all jobs in :attr:~stages.BuildSteps.stages` using a worker pool.
        """

        if workers is None:
            logger.debug('no worker specified to run(), using the class default.')
            workers = self.workers()

        p = Pool(processes=workers)
        logger.info('created working pool with {0} workers'.format(workers))

        for job in self.stage:
            if isinstance(job[1], dict):
                p.apply_async(job[0], kwds=job[1])
            else:
                p.apply_async(job[0], job[1])
            logger.info('calling job ({0}) operation asynchronously'.format(job[0].__name__))

        p.close()
        logger.info('now waiting for jobs to finish.')
        p.join()
        logger.debug('completed worker pool for stage.')


class BuildSequence(BuildSteps):
    """
    A subclass of :class:~stages.BuildSteps` that executes jobs in the order
    they were added to the :class:~stages.BuildSteps` object.
    """

    def run(self, *args, **kwargs):
        """Runs all jobs in :class:~stages.BuildSteps` in the order they were
        added to the object. Ignores all arguments."""

        logger.info('running jobs in a build sequence.')
        for job in self.stage:
            logger.info('running {0}'.format(job[0].__name__))
            job[0](*job[1])

class BuildSystem(object):
    """
    A representation of a multi-stage build system that combines a number build
    stages to be constructed in any order, and executed sequentially.
    """

    def __init__(self, initial_stages=None):
        """
        :param BuildSteps initial_stages: A :class:~stages.BuildSteps` object or
           list of :class:~stages.BuildSteps` objects that define a series of
           build steps.

        If ``initial_stages`` is a list, the resulting
        :class:~stages.BuildSystem`  object will assume the order of the
        :class:~stages.BuildSteps` list.
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

        if initial_stages is not None:
            logger.debug('creating BuildSystem object with a default set of stages.')
            if isinstance(initial_stages, list):
                for stage in initial_stages:
                    self.add_stage(stage)
            else:
                self.add_stage(initial_stages)

        logger.info('created BuildSystem object.')

    @property
    def closed(self):
        """
        :returns: ``True`` when after finalizing a :class:~stages.BuildSystem`
           object.
        """
        return not self.open

    @property
    def strict(self):
        """
        A Getter and setter for the :attr:~stages.BuildSystem._strict` setting.
        """
        return self._strict

    @strict.setter
    def strict(self, value):
        logger.info('changing default object strictness setting.')
        self._strict = value

    def close(self):
        "Sets the :attr:`~stages.BuildSystem.open` value to ``False``."
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

        Special case and wrapper of :meth:~stages.BuildSystem.add_stage()` that
        adds a new stage without adding any jobs to that stage.
        """

        logger.info('creating a new stage named {0}'.format(name))
        self.add_stage(name, stage=None)

    def extend(self, system):
        """
        :param BuildSystem system: A :class:`~stages.BuildSystem()` object.

        Takes ``system`` and grows the current :class:`~stages.BuildSystem()`
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
           :meth:~stages.BuildSystem.new_stage()`.

        :param string stage_type: Either ``sequence`` (or ``seq``) or ``stage``
           to determine what kind of :class`~stages.BuildSteps()` object to
           instantiate if ``stage`` is ``None``

        :param bool strict: Overrides the default
           :attr:`~stages.BuildSystem.strict` attribute. When ``True``, prevents
           callers from adding duplicate stages to a :class:~stages.BuildSystem`
           object.

        :raises: :err:`~err.InvalidStage()` in strict mode if ``name`` or
           ``stage`` is malformed.

        Creates a new stage and optionally populates the stage with tasks. Note
        the following behaviors:

        - If ``name`` exists in the current :class:~stages.BuildSystem`,
          ``strict`` is ``False``, and ``stage`` is ``None``; then
          :meth:~stages.BuildSystem.add_stage()` adds the stage with ``name`` to
          the current :class:~stages.BuildSystem` object. This allows you to
          perform the same stage multiple times in one build process.

        - If ```name`` does not exist in the current
          :class:~stages.BuildSystem`, and ``stage`` is ``None``,
          :meth:~stages.BuildSystem.add_stage()` adds the stage and instantiates
          a new :class`~stages.BuildSteps()` (either
          :class`~stages.BuildSequence()` or :class`~stages.BuildStage()`
          depending on the value of ``stage_type``) object with ``name`` to the
          current :class:~stages.BuildSystem` object.

          :meth:~stages.BuildSystem.add_stage()` must specify a ``stage_type``
          if ``stage`` is ``None``. When ``strict`` is ``True`` not doing so
          raises an exception.

        - Adds the ``stage`` with the specified :class`~stages.BuildSteps()`
          object to the :class:~stages.BuildSystem` object. Raises an exception
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
           :class:`~stages.BuildSystem`.

        :returns: The position of the stage in the :class:`~stages.BuildSystem`,
           or ``None`` if it doesn't exist in the :class:`~stages.BuildSystem`
           object.
        """

        if stage in self._stages:
            return self._stages.index(stage)
        else:
            return None

    def count(self):
        """
        :returns: The number of stages in the :class:~stages.BuildSystem` object.
        """
        return len(self._stages)

    def stage_exists(self, name):
        """
        :param string name: The name of a possible stage in the
           :class:~stages.BuildSystem` object.

        :returns: ``True`` if the stage exists in :class:~stages.BuildSystem`
           and ``False`` otherwise.
        """

        if name in self._stage:
            return True
        else:
            return False

    def run_stage(self, name, strict=None):
        """
        :param string name: The potential name of a stage in the
           :class:~stages.BuildSystem` object.

        :param bool strict: Defaults to :attr:`~stages.BuildSystem.strict`.

        :returns: ``False`` if ``name`` is not in the
           :class:~stages.BuildSystem` object, and ``strict`` is
           ``False``. In all other cases
           :meth:`~stages.BuildSystem.run_stages()` returns ``True`` after the
           stage runs.

        :raises: :exc:`~err.StageRunError` if ``strict`` is ``True`` and
           ``name`` does not exist.

        Runs a single stage from the :class:~stages.BuildSystem` object.
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

        :param bool strict: Defaults to :attr:`~stages.BuildSystem.strict`.

        :raises: :exc:`~err.StageRunError` if ``strict`` is ``True`` and
           :attr:`~stages.BuildSystem.open` is ``True``.

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
        :param bool strict: Defaults to :attr:`~stages.BuildSystem.strict`.

        :raises: :exc:`~err.StageRunError` if ``strict`` is ``True`` and
           :attr:`~stages.BuildSystem.open` is ``True``.

        Calls the :meth:`~stages.BuildSteps.run()` method of each stage object.
        """
        logger.info('running entire build system')
        self.run_part(idx=self.count() - 1, strict=strict)

class BuildSystemGenerator(object):
    """
    :class:`~stages.BuildSystemGenerator` objects provide a unifying interface
    for generating and running :class:`~stages.BuildSystem` objects from
    easy-to-edit sources. :class:`~stages.BuildSystemGenerator` is the
    fundamental basis of the :ref:`buildc` tool.

    :param dict funcs: Optional. A dictionary that maps callable objects
       (values), to identifiers used by build system definitions. If you do not
       specify.

    :class:`~stages.BuildSystemGenerator` is designed to parse streams of YAML
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
        :meth:`~stages.BuildSystemGenerator.finlize()` for more information."""

        logger.info('created build system generator object')

    def finalize(self):
        """
        :raises: :exc:`~err.InvalidBuildSystem` if you call
           :meth:`~stages.BuildSystemGenerator.finalize()` more than once on a
           single :class:`~stages.BuildSystemGenerator()` object.

        You must call :meth:`~stages.BuildSystemGenerator.finalize()` before
        running the build system.

        :meth:`~stages.BuildSystemGenerator.finalize()` compiles the build
        system. If there are no tasks with dependencies,
        :attr:`~stages.BuildSystemGenerator._stages` becomes the
        :attr:`~stages.BuildSystemGenerator.system` object. Otherwise,
        :meth:`~stages.BuildSystemGenerator.finalize()` orders the tasks with
        dependencies, inserts them into a :class:`~stages.BuildSequence` object
        before inserting the :attr:`~stages.BuildSystemGenerator._stages` tasks.
        """

        if self._final is False and self.system is None:

            if len(self._process_tree) == 0:
                logger.debug('no dependency tasks exist, trying to add build stages.')
                if self._stages.count() > 0:
                    self.system = self._stages
                    logger.info('added tasks from build stages to build system.')
                else:
                    logger.critical('cannot finalize empty generated BuildSystem object.')
                    raise InvalidBuildSystem

            elif len(self._process_tree) > 0:
                self.system = BuildSystem()

                self._process = topological_sort(self._process_tree)
                logger.debug('successfully sorted dependency tree.')

                for i in self._process:
                    self.system.add_stage(i, self._process_jobs[i][0], self._process_jobs[i][1])

                if self._stages.count() > 0:
                    self.system.extend(self._stages)
                    logger.info('added stages tasks to build system.')

            self.system.close()

        else:
            logger.critical('cannot finalize object')
            raise InvalidBuildSystem

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
        :class:`~stages.BuildSystem()` object.
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

        Adds a callable object to the :attr:`~stages.BuildSystemGenerator.funcs`
        attribute with the identifier ``name``.
        """
        if not isinstance(func, types.FunctionType):
            logger.critical('cannot add tasks that are not callables ({0}).'.format(name))
            raise InvalidJob("{0} is not callable.".format(func))

        logger.debug('adding task named {0}'.format(name))
        self.func[name] = func

    def ingest_yaml(self, filename):
        """
        :param string filename: The fully qualified path name of a :term:`YAML`
           file that contains a build system specification.

        For every document in the YAML file specified by ``filename``, calls
        :meth:`~stages.BuildSystemGenerator._process_job()` to add that job to
        the :attr:`~stages.BuildSystemGenerator.system` object.
        """

        logger.debug('opening yaml file {0}'.format(filename))
        with open(filename, 'r') as f:
            try:
                jobs = yaml.safe_load_all(f)
            except NameError:
                msg = 'attempting to load a yaml definition without PyYAML installed.'
                logger.critical(msg)
                raise StageRunError(msg)

            job_count = 0
            for spec in jobs:
                self._process_job(spec)
                job_count += 1

        logger.debug('loaded {0} jobs from {1}'.format(job_count, filename))

    def ingest_json(self, filename):
        """
        :param string filename: The fully qualified path name of a :term:`JSON`
           file that contains a build system specification.

        For every document in the JSON file specified by ``filename``, calls
        :meth:`~stages.BuildSystemGenerator._process_job()` to add that job to
        the :attr:`~stages.BuildSystemGenerator.system` object.
        """

        logger.debug('opening json file {0}'.format(filename))
        with open(filename, 'r') as f:
            jobs = json.load(f)

            for spec in jobs:
                self._process_job(spec)

        logger.debug('loaded {0} jobs from {1}'.format(job_count, filename))

    def _process_stage(self, spec, spec_keys):
        """
        :param dict spec: The task specification imported from user input.

        :param set spec_keys: A set containing the top level keys in the set.

        :returns: A two item tuple, containing a function and a list of arguments.

        :raises: :exc:`~err.InvalidJob` if the schema of ``spec`` is not recognized.

        Based on the schema of the ``spec``, creates tasks and sequences to add
        to a BuildSystem using, as appropriate one of the following methods:

        - :meth:`~stages.BuildSystemGenerator.generate_job()`,
        - :meth:`~stages.BuildSystemGenerator.generate_shell_job()`, or
        - :meth:`~stages.BuildSystemGenerator.generate_sequence()`.
        """

        spec_keys = set(spec.keys())

        if self.funcs and spec_keys.issuperset(set('job', 'args', 'stage')):
            logger.debug('spec looks like a pure python job, processing now.')
            return self.generate_job(spec, self.funcs)
        elif spec_keys.issuperset(set('dir', 'cmd', 'args', 'stage')):
            logger.debug('spec looks like a shell job, processing now.')
            return self.generate_shell_job(spec)
        elif self.funcs and spec_keys.issuperset(set('stage', 'tasks')):
            logger.debug('spec looks like a shell job, processing now.')
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

        Wraps :meth:`~stages.BuildSystemGenerator._process_stage()` and
        additionally modifies the internal strucutres associated with the
        dependency tree.
        """

        job = _process_stage(spec)

        self._process_jobs[spec['target']] = job
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
