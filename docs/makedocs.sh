#!/bin/bash

# Assume Sphinx and the ReadTheDocs theme installed.
# Documentation placed in _build/html
#
# If not installed, run:
# pip3 -install -r requirements.txt

# Use a config that doesn't require vault when generating docs.
export DJANGO_SETTINGS_MODULE=boss.settings.mysql

sphinx-apidoc -f -o . ../django
make html
