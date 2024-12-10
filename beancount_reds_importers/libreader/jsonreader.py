#!/usr/bin/env python3

"""JSON reader for beancount-reds-importers.

JSON files have widely varying specifications, and thus, this is a very generic reader, and most of
the logic will have to be the institution specific readers.

"""

import json

from beancount.ingest import importer

from beancount_reds_importers.libreader import reader


class Importer(reader.Reader, importer.ImporterProtocol):
    FILE_EXTS = ["json"]

    def initialize_reader(self, file):
        if getattr(self, "file", None) != file:
            self.file = file
            self.reader_ready = False
            with open(file.name, "r") as f:
                self.json_data = json.load(f)
            self.reader_ready = self.deep_identify(file)
        if self.reader_ready:
            self.set_currency()

    def deep_identify(self, file):
        """For overriding by institution specific importer which can check if an account name
        matches, and other such things."""
        # default value to False, else jsonreader.initialize_reader fail to execute because missing attribut "config"
        return False

    def file_date(self, file):
        """Get the ending date of the statement."""
        if not getattr(self, "json_data", None):
            self.initialize(file)
        # TODO:
        return None

    def read_file(self, file):
        with open(file.name, "r") as f:
            self.json_data = json.load(f)

    def get_json_elements(self, json_path, json_interpreter=lambda x: x):
        """Extract a list of elements in the JSON file at the given JSON path. Typically,
        transactions are stored in a JSON path, and this extracts them."""
        elements = self.json_data
        for key in json_path.split("."):
            if key in elements:
                elements = elements[key]
            else:
                return []
        for elem in elements:
            yield json_interpreter(elem)

    def get_transactions(self):
        """/Transactions/Transaction is a dummy default path for transactions that needs to be
        overriden in the institution specific importer."""
        yield from self.get_json_elements("Transactions.Transaction")
