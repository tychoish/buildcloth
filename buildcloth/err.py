# Copyright 2012-2013 10gen, Inc.
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

class BuildClothError(Exception):
    """
    :class:`~cloth.BuildClothError` is the primary exception base class for
    Buildcloth.

    When raised with a string, the resulting exception will return the error
    message.
    """
    def __init__(self, msg=None):
        """
        :param string msg: A message to include with the exception. Defaults to
                           ``None``.
        """

        self.msg = msg
        "A message included  exception message."

    def __str__(self):
        if self.msg is None:
            return "Error constructing buildfile."
        else:
            return "Error: " + self.msg

class BuildClothBaseError(BuildClothError):
    "Base error class for all generated build file errors."

class MalformedBlock(BuildClothBaseError):
    "Raised when attempting to insert an invalid block."
    pass

class DuplicateBlock(BuildClothBaseError):
    "Raised when inserting a duplicate block to avoid overwriting data."
    pass

class MalformedRawContent(BuildClothBaseError):
    "Raised when attempting to insert malformed raw content directly to a build system object."
    pass

class MalformedContent(BuildClothBaseError):
    "Raised when attempting to insert malformed content to builder."
    pass

class InvalidBuilder(BuildClothBaseError):
    "Raised when a :attr:`~cloth.BuildCloth.builder` block is not valid."
    pass

class MissingBlock(BuildClothBaseError):
    """
    Raised when attempting to access a :attr:`~cloth.BuildCloth.builder` block
    that does not exit.
    """
    pass

class NinjaClothError(BuildClothBaseError):
    """
    Raised by the Ninja interface when constructing Ninja builders.
    """
    pass

class InvalidRule(BuildClothBaseError):
    "Raised when attempting to specify an impossible in :mod:`rules`."
    pass

#################### Build Stages Errors ####################

class BuildStagesError(BuildClothError):
    "Base error class for all build stage errors."
    pass

class InvalidStage(BuildStagesError):
    """
    Raised when an element in a :class:`~stages.BuildSystem` or
    :class:`~stages.BuildSteps` object is malformed or erroneous. Only the
    "strict" modes will raise this exception, and would otherwise return
    ``False``.
    """
    pass

class InvalidJob(BuildStagesError):
    """
    Raised when attempting to add or modify an invalid job in a build system.
    """
    pass

class StageClosed(BuildStagesError):
    """Raised when attempting to modify or re-close a finalized build
    :class:`~stages.BuildSystem` or :class:`~stages.BuildSteps` object."""
    pass

class StageRunError(BuildStagesError):
    """Raised when attempting to run build system jobs."""
    pass

class InvalidSystem(BuildStagesError):
    """Raised when attempting to manipulate build invalid BuildSystem
    objects."""
    pass
