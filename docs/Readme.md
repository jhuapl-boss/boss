# Generating HTML Documentation

Note that your system will need Django and the Django Rest Framework to
properly generate the documentation since it loads the Python files as it
creates the documentation.

`$BOSS` is the location of the boss repository.

```shell
cd $BOSS/docs

# Ensure Sphinx and the ReadTheDocs theme is available.
pip3 install -r requirements.txt

./makedocs.sh
```

Documentation will be placed in `$BOSS/docs/_build/html`.
