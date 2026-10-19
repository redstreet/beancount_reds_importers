from beangulp import cache

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Amazon Retail Orders Importer"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = ""
        self.header_identifier = ""
        # fmt: off
        self.column_labels_line = '"ASIN","Billing Address","Carrier Name & Tracking Number","Currency","Department","Gift Message","Gift Recipient Contact","Gift Sender Name","Item Serial Number","Order Date","Order ID","Order Status","Original Quantity","Payment Method Type","Product Condition","Product Name","Purchase Order Number","Ship Date","Shipment Item Subtotal","Shipment Item Subtotal Tax","Shipment Status","Shipping Address","Shipping Charge","Shipping Option","Total Amount","Total Discounts","Unit Price","Unit Price Tax","Website"'

        self.file_encoding = "utf-8-sig"  # Amazon files have BOM
        self.header_map = {
            "Order Date":     "date",
            "Product Name":   "payee",
            "Order ID":       "memo",
            "Total Amount":   "amount",
            "Currency": "currency",
        }
        self.transaction_type_map = {
            "":     "transfer",
        }
        # fmt: on
        self.skip_transaction_types = []

    def deep_identify(self, file):
        return self.column_labels_line in cache.get_file(file).head()

    def prepare_processed_table(self, rdr):
        rdr = rdr.convert("amount", lambda i: -i)
        return rdr

    def build_metadata(self, file, metatype=None, data={}):
        default = super().build_metadata(file, metatype, data)

        if metatype == "transaction":
            payment = {"payment_method": data["transaction"].Payment_Method_Type}
            discounts = {"total_discounts": data["transaction"].Total_Discounts}
            return {**default, **payment, **discounts}

        return default
