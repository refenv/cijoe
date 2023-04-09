Creating Packages
=================

Let's create a package for ``blob``. Assuming a lot of things, e.g. that you
have a bunch of repositories in ``$HOME/git``, among them **cijoe** itself, and
the name of your project is ``blob``. Then create a skeleton like below, using
files from the **cijoe** repository::

  # Create a directory and cd into it
  mkdir $HOME/git/cijoe-pkg-blob
  cd $HOME/git/cijoe-pkg-blob

  # Copy files from the cijoe Python package
  cp $HOME/git/cijoe/.gitignore .
  cp $HOME/git/cijoe/.pre-commit-config.yaml .
  cp $HOME/git/cijoe/pyproject.toml .
  cp $HOME/git/cijoe/requirements.txt .

  # Copy and adjust these with your and your projects name
  cp $HOME/git/cijoe/LICENSE .
  cp $HOME/git/cijoe/Makefile .
  cp $HOME/git/cijoe/setup.py .

Then create the actual package content layout::

  # The deep nesting is because cijoe uses namespace packages
  mkdir -p src/cijoe/blob
  mkdir -p src/cijoe/blob/{selftest,tests,scripts,workflows,configs}
  touch src/cijoe/blob/__init__.py
  touch src/cijoe/blob/{selftest,tests,scripts,workflows,configs}/__init__.py

  # If you are putting it on GitHUB, set the passwords on your repos
  cp -r $HOME/git/cijoe/.github .
  git init
  git add .
  git commit -s -m "Initial commit"

That should give you a skeleton.
