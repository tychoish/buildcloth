=================
Buildcloth README
=================

You can download `buildcloth from pypi
<https://pypi.python.org/pypi/buildcloth>`_, or `read the
documentation <http://cyborginstitute.org/projects/buildcloth>`_ for a
complete introduction to Buildcloth.

Overview
--------

Buildcloth is a Python library for specifying and maintaining build
system descriptions (e.g. :term:`Makefile` and :term:`ninja.build`
files,) using to encode build logic and generation. Buildcloth is
great for projects that: 

- want to encode the logic of build processes in Python rather than
  in a build system's own syntax *but* don't want to implement a
  custom build automation tool.

- want to integrate components and data from Python applications or
  other data sources without needing to maintain cumbersome and
  redundant build scripts.

- want to use familiar unit testing tools to ensure correctness for
  build systems.

Features
--------

- Buildcloth provides interface for generating both `Ninja`_ and
  `Make`_ build systems.
  
- Buildcloth is agnostic about your approach to storing build
  generator data: the build cloth system may generate build system
  from YAML files, database systems, or derive information from the
  source directly.

- Buildcloth minimizes the amount of Make or Ninja-specific knowledge
  required to engineer an effective build system. At the same time,
  the build-system output can be *very* human readable, which makes
  debugging easier and minimizes dependence on buildcloth.
  
- Buildcloth is attempting to insulate build system implementation
  from your build system, making it easier to transition between (and
  test) Make, Ninja, and potentially other tools.

.. _`Ninja`:http://martine.github.com/ninja/
.. _`Make`:http://www.gnu.org/software/make/manual/make.html
  
Use
---

See the `project documentation
<http://cyborginstitute.org/projects/buildcloth>`_ for full usage
information. In particular, consider the `api reference
<http://cyborginstitute.org/projects/buildcloth/api/>`_ and the
`general tutorial
<http://cyborginstitute.org/projects/buildcloth/tutorial/>`_.

Project Information
-------------------

- `Issue Tracker <https://issues.cyborginstitute.net/describecomponents.cgi?product=buildcloth>`_
- `git repository <http://git.cyborginstitute.net/?p=buildcloth.git>`_
- `github <http://github.com/tychoish/buildcloth/>`_
- `documentation <http://cyborginstitute.org/projects/buildcloth>`_
- `pypi <https://pypi.python.org/pypi/buildcloth>`_
