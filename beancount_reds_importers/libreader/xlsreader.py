"""xlsx importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import petl as etl
import re
from beancount_reds_importers.libreader import csvreader
from os import devnull


class Importer(csvreader.Importer):
    FILE_EXTS = ['xls']

    def initialize_reader(self, file):
        if getattr(self, 'file', None) != file:
            self.file = file
            self.file_read_done = False
            self.reader_ready = False

            # TODO: this reads the entire file. Chop off after perhaps 2k or n lines
            rdr = self.read_raw(file)
            header = ''
            for r in rdr:
                line = ''.join(str(x) for x in r)
                header += line

            # TODO
            # account_number = self.config.get('account_number', '')
            # self.reader_ready = re.match(self.header_identifier, file.head()) and \
            #                     account_number in file.head()

            if re.match(self.header_identifier, header):
                self.reader_ready = True

    def read_raw(self, file):
        # set logfile to ignore WARNING *** file size (92598) not 512 + multiple of sector size (512)
        return etl.fromxls(file.name, logfile=open(devnull, 'w'))
