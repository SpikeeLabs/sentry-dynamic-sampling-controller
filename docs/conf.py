# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

import django

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath(".events.py"))

os.environ["DJANGO_SETTINGS_MODULE"] = "controller.settings"
django.setup()


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Sentry Dynamic Sampling Controller"
copyright = "2023, jeanloup.monnier <jean-loup.monnier@spikeelabs.fr>"
author = "jeanloup.monnier <jean-loup.monnier@spikeelabs.fr>"
release = "1.3.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinxcontrib_django",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinxcontrib.mermaid",
    "sphinxcontrib.httpdomain",
    "sphinx.ext.autosummary",
    "celery.contrib.sphinx",
    "m2r2",
]


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


# -- Options for napleon extensions ------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True

intersphinx_mapping = {
    "celery": ("https://docs.celeryproject.org/en/stable/", None),
    "django": ("http://docs.djangoproject.com/en/dev/", "http://docs.djangoproject.com/en/dev/_objects/"),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
}

source_suffix = [".rst", ".md"]
