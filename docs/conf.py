# -*- coding: utf-8 -*-
#
# High Level Systems Administration documentation build configuration file, created by
# sphinx-quickstart on Thu Oct 20 09:29:36 2011.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys, os

project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
from bootstrap import buildsystem, master_conf
sys.path.append(os.path.join(project_root, buildsystem))
from utils.config import get_conf

conf = get_conf(project_root)

sys.path.insert(0, os.path.abspath(os.path.join('..', 'buildcloth/')))
sys.path.insert(0, os.path.abspath('..'))

# -- General configuration -----------------------------------------------------

needs_sphinx = '1.0'
extensions = ["sphinx.ext.intersphinx", "sphinx.ext.extlinks", "sphinx.ext.autodoc"]
templates_path = ['.templates']
source_suffix = '.txt'
master_doc = 'index'

# General information about the project.
project = u'Buildcloth, a Build-system Generator'
copyright = u'2012-2013, Contributors'

import buildcloth
version = buildcloth.__version__
release = version

exclude_patterns = []
pygments_style = 'sphinx'

extlinks = {
    'project': ('/projects/%s', ''),
    'institute': ('http://cyborginstitute.com/%s', ''),
    'issues': ('http://issues.cyborginstitute.com/%s', ''),
    'list': ('http://lists.cyborginstitute.com/listinfo/%s', ''),
    'git': ('http://git.cyborginstitute.com/%s', ''),
    'github': ('http://github.com/cyborginstitute/%s', '')
    }

intersphinx_mapping = {
        'python' : ('http://docs.python.org/2/', '../build/python.inv'),
        'gevent': ('http://www.gevent.org/', '../build/gevent.inv'),
      }


# -- Options for HTML output ---------------------------------------------------

html_theme = 'cyborg'
html_theme_path = [os.path.join(conf.paths.projectroot, conf.paths.buildsystem, 'themes')]
html_static_path = ['.static']

html_use_smartypants = True
html_theme_options = {
    'project': conf.project.name,
    'ga_code': 'UA-2505694-4'
}

html_sidebars = {
    '**': ['localtoc.html', 'relations.html', 'sourcelink.html'],
}

#html_title = None
#html_short_title = None
#html_logo = None
#html_favicon = None

html_use_index = True
html_show_sourcelink = False
html_show_sphinx = False
html_show_copyright = True
htmlhelp_basename = conf.project.name
