"""tsv (tab separated values) importer module for beancount to be used along with investment/banking/other
importer modules in beancount_reds_importers."""


from beancount.ingest import importer
import petl as etl
from beancount_reds_importers.libreader import csvreader


class Importer(csvreader.Importer, importer.ImporterProtocol):
    FILE_EXTS = ['tsv']

    def read_raw(self, file):
        return etl.fromtsv(file.name)
