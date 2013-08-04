=================
Buildcloth README
=================

You can download `buildcloth from pypi
<https://pypi.python.org/pypi/buildcloth>`_, or `read the
documentation <http://cyborginstitute.org/projects/buildcloth>`_ for a
complete introduction to Buildcloth.

Overview
--------

Buildcloth is a Python library for specifying build systems. You can
think of Buildcloth as a meta-build toolkit, but it's really about
defining and maintaining complex multi-stage processes as easily as
possible. There are three different tools in the buildcloth toolkit:

- Simple procedural interfaces for generating build system definition
  files for `Make`_ and `Ninja`_, in easy to use Python.

- A higher level cross-tool abstraction layer for specifying
  build-rules that you can use to generate :term:`Makefile` and
  :term:`ninja.build` output.

- A simple stage-based Python tool for defining and running concurrent
  (i.e. multiprocessing) Python-based build systems with minimal
  overhead.

Although these components are distinct and are available for
independent use, they provide a basis for building and combining
ad-hoc tools to orchestrate and implement build systems, without
risking insanity or fragility.

Features
--------

- Buildcloth is agnostic about your approach to storing build
  generator data: the build cloth system may generate build systems
  from YAML or JSON files, database systems, derive information from
  the source directly.

- If you're comfortable with basic Python code and understand your
  build process, you can use Buildcloth.

  For generating Make and Ninja files, Buildcloth minimizes the amount
  of Make or Ninja-specific knowledge required to engineer an
  effective build system. At the same time, the build-system output
  can be *very* human readable, which makes debugging easier and
  minimizes dependence on buildcloth.

  For stage-based builds, Buildcloth provides straight forward
  idiomatic Python tools for defining a build system.

- Buildcloth is attempting to insulate build system implementation
  from your build system, making it easier to transition between (and
  test) Make, Ninja, and potentially other custom tools.

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
