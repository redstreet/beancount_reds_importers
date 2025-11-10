#!/usr/bin/env python3
"""Import configuration."""

import sys
from os import path

import beangulp
from smart_importer import PredictPostings

sys.path.insert(0, path.join(path.dirname(__file__)))

from beancount_reds_importers.importers import ally

# Setting this variable provides a list of importer instances.
CONFIG = [
    # Banks and credit cards
    # --------------------------------------------------------------------------------------
    ally.Importer(
        {
            "account_number": "23456",
            "main_account": "Assets:Banks:Checking",
        }
    )
]

HOOKS = [PredictPostings().hook]

if __name__ == "__main__":
    ingest = beangulp.Ingest(CONFIG, HOOKS)
    ingest()
