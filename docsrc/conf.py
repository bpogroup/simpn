import os
import sys
import sphinx_readable_theme

sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../../simpn/'))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'SimPN'
copyright = '2023, Remco Dijkman'
author = 'Remco Dijkman'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.githubpages',
    'autodocsumm',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

autodoc_default_options = {
    'autosummary': True,
}

autodata_content = 'both'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme_path = [sphinx_readable_theme.get_html_theme_path()]
html_theme = 'readable'
html_sidebars = {
   '**': ['globaltoc.html', 'searchbox.html'],
   'using/windows': ['windowssidebar.html', 'searchbox.html'],
}