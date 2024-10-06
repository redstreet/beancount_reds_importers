"""XML reader for beancount-reds-importers.

XML files have widely varying specifications, and thus, this is a very generic reader, and most of
the logic will have to be the institution specific readers.

"""

from beancount.ingest import importer
from lxml import etree

from beancount_reds_importers.libreader import reader


class Importer(reader.Reader, importer.ImporterProtocol):
    FILE_EXTS = ["xml"]

    def initialize_reader(self, file):
        if getattr(self, "file", None) != file:
            self.file = file
            self.reader_ready = False
            self.xmltree = etree.parse(file.name)
            self.reader_ready = self.deep_identify(file)
        if self.reader_ready:
            self.set_currency()

    def deep_identify(self, file):
        """For overriding by institution specific importer which can check if an account name
        matches, and oother such things."""
        return True

    def file_date(self, file):
        """Get the ending date of the statement."""
        if not getattr(self, "xmltree", None):
            self.initialize(file)
        # TODO:
        return None

    def read_file(self, file):
        self.xmltree = etree.parse(file.name)

    def get_xpath_elements(self, xpath_expr, xml_interpreter=lambda x: x):
        """Extract a list of elements in the XML file at the given XPath expression. Typically,
        transactions are stored in an xml path, and this extracts them."""
        elements = self.xmltree.xpath(xpath_expr)
        for elem in elements:
            yield xml_interpreter(elem.attrib)

    def get_transactions(self):
        """/Transactions/Transaction is a dummy default path for transactions that needs to be
        overriden in the institution specific importer."""
        yield from self.get_xpath_elements("/Transactions/Transaction")
