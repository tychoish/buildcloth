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
:mod:`stages` is part of a component in a complete a complete system tool that provides abstractions for groups


Tasks (i.e. functions) are the smallest unit of work, and are typically Python
functions, although a task may be shell commands in some cases. :mod:`stages`
allows you to specify two basic relationships between tasks:

*Sequence*
   A series of tasks which must be executed in a specific order. Provided by
   :class:`~stages.BuildSequence()`.

   A group of tasks that can be executed in any order, and potentially
   concurrently. Provided by :class:`~stages.BuildStage()`.

*Stage*
   A series of tasks that may execute in parallel.

:class:`~stages.BuildSequence()` and :class:`~stages.BuildStage()` share the
same base class (:class:`~stages.BuildSteps()`) and have a common interface
despite different behaviors.
"""

import types
import logging
from multiprocessing import cpu_count, Pool

from buildcloth.err import InvalidStage, StageClosed, StageRunError, InvalidJob, InvalidSystem
from buildcloth.utils import is_function

logger = logging.getLogger(__name__)

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

        if not is_function(stage[0]):
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

        :returns: ``True`` upon completion.
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
        return True


class BuildSequence(BuildSteps):
    """
    A subclass of :class:~stages.BuildSteps` that executes jobs in the order
    they were added to the :class:~stages.BuildSteps` object.

    :returns: ``True`` upon completion.
    """

    def run(self, *args, **kwargs):
        """Runs all jobs in :class:~stages.BuildSteps` in the order they were
        added to the object. Ignores all arguments."""

        logger.info('running jobs in a build sequence.')
        for job in self.stage:
            logger.info('running {0}'.format(job[0].__name__))
            job[0](*job[1])

        return True
