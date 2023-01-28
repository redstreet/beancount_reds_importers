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
