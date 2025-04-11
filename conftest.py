# This adds the pytest --generate option.  See
# https://github.com/beancount/beancount/blob/v2/examples/ingest/office/importers/conftest.py
#
# pylint: disable=invalid-name
pytest_plugins = "beancount_reds_importers.util.regression_pytest"
