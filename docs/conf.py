# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PICNIC'
copyright = '2026, The NYSPI MIND Brain Imaging Lab'
author = 'The NYSPI MIND Brain Imaging Lab'
release = '0.2.1'


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_rtd_theme',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
# html_static_path = ['_static']


# -- Include PICNIC source code in this documentation --------------------------
import sys, os
sys.path.insert(0, os.path.abspath('../src'))

# The docs CI image only installs Sphinx, not PICNIC's runtime dependencies.
# Mock them so autodoc can import our modules and read their docstrings.
autodoc_mock_imports = [
    'FreeSimpleGUI', 'PIL', 'matplotlib', 'nibabel', 'nilearn', 'nipype',
    'numpy', 'pandas', 'rich', 'scipy', 'six', 'templateflow',
]
