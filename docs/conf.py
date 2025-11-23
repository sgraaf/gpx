"""Sphinx configuration."""

from importlib import metadata

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "PyGPX"
copyright_ = "2021, Steven van de Graaf"
author = "Steven van de Graaf"
# The full version, including alpha/beta/rc tags.
release = metadata.version("gpx")
# The short X.Y version.
version = release.rsplit(".", 1)[0]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinxext.opengraph",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# auto-generate header anchors
myst_heading_anchors = 3

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# move type hints into the description block, instead of the signature
autodoc_member_order = "bysource"
autodoc_default_options = {
    "show-inheritance": True,
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "top_of_page_button": None,
}
