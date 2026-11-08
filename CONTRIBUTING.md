# Contributing

Contributions welcome. Preferably:
- include a test file. I realize this is sometimes a pain to create, but there is no way
  for me to test external contributions without test files
- keep importers simple. See the average length of an existing, comparable importer. If
  your importer is significantly longer, that is a good indication that it could be
  simplified further
- use [conventional commit messages](https://www.conventionalcommits.org/). Simply see
  the last few commits, and it should be apparent how to prefix your commit (usually
  with a `feat:` for new importers)
- directory structure should follow this example:
  ```
   └── importers                     <-- default importer
       └── fidelity
           ├── __init__.py
           ├── fidelity_cma_csv.py   <-- secondary importer for the same institution
           └── fidelity_cma_csv_examples
               ├── fidelity-cma-csv.import
               ├── History_for_Account_X8YYYYYYY.csv
               └── run_test.bash
  ```

## Setup

Development setup would typically look something like this:

```bash
# clone repo, cd to repo

# create virtual environment
python3 -m venv venv

# activate virtual environment
source venv/bin/activate

# install dependencies
pip install -e .[dev]
```

Alternatively, use the same locked dependencies as CI:

```bash
uv sync --locked --all-extras
uv run --no-sync pytest --cov
uv run --no-sync coverage report --include='*/libreader/*.py,*/libtransactionbuilder/*.py' --fail-under=85
```

The shared readers and transaction builders have an 85% combined line and branch
coverage gate. Coverage reports also include untested importer modules; there is no
whole-project percentage gate yet. Tests must run offline with anonymized or synthetic
data. Mock downloads and subprocess commands rather than using real accounts.

For a bug fix, add a test that reproduces the defect. For a new importer, include a
representative fixture and reviewed expected output. Generate expectations only for
the intended test directory, inspect the diff, and run pytest without `--generate`
before committing. Never regenerate expectations merely to make a failing test pass.

## Changes and pull requests

The maintainer can push directly to `main`; contributors submit pull requests.
Both paths run CI. A failed direct push remains on `main` until a follow-up fix.
For PRs, wait for **All checks** and **PR title** to pass before merging.

Use Conventional Commit messages for direct pushes and Conventional Commit PR titles.
Prefer squash merges so the PR title becomes the commit used for release notes.
Use `fix:` for patches, `feat:` for features, and `!` or a `BREAKING CHANGE:` footer
for incompatible changes. The release bot maintains a separate PR; only the maintainer
decides when to merge it. See [RELEASING.md](RELEASING.md).

## Package checks

```bash
uv run --no-sync python -m build --no-isolation
uv run --no-sync twine check dist/*
uv run --no-sync python scripts/check_distribution.py dist
```

Use an empty `dist` directory for each build; the check intentionally rejects stale
extra artifacts. Clean-install checks resolve runtime dependencies from PyPI, so
they need network access (or a populated uv cache). Run them on Linux. Python 3.15
currently builds Beancount from source and requires `m4` and a C compiler.

Update dependencies deliberately with `uv lock --upgrade`, run the checks, and commit
`uv.lock` with the change. Build tools are locked too. A weekly CI run tests fresh
dependency resolutions without modifying the committed lockfile; failures appear in
the Actions tab and normal GitHub workflow notifications.

## Formatting

Prior to finalizing a pull request make sure to run the formatting tools and
commit any resulting changes.

```bash
uv run --no-sync ruff check .
uv run --no-sync ruff format
uv run --no-sync isort .
```
