#             config={ Col.LAST4: "Payment Instrument Type", },
#             invert_sign=True,
#             regexps=(
#                 "Website", "Order ID", "Order Date", "Purchase Order Number",
#                 "Currency", "Unit Price", "Unit Price Tax", "Shipping Charge",
#                 "Total Discounts", "Total Owed", "Shipment Item Subtotal",
#                 "Shipment Item Subtotal Tax", "ASIN", "Product Condition",
#                 "Quantity", "Payment Instrument Type", "Order Status",
#                 "Shipment Status", "Ship Date", "Shipping Option",
#                 "Shipping Address", "Billing Address",
#                 "Carrier Name & Tracking Number", "Product Name",
#                 "Gift Message", "Gift Sender Name",
#                 "Gift Recipient Contact Details",
#             ),


from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Amazon Retail Orders Importer"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = ""
        self.header_identifier = ""
        # self.column_labels_line = '"Date","Status","Type","CheckNumber","Description","Withdrawal","Deposit","RunningBalance"'
        self.date_format = "%m/%d/%Y"
        self.file_encoding = "utf-8-sig"  # Amazon files have BOM
        # fmt: off
        self.header_map = {
            "Order Date":     "date",
            "Product Name":   "payee",
            "Order ID":        "memo",
            "Total Owed":     "amount",
            "Currency": "currency",
        }
        self.transaction_type_map = {
            "":     "transfer",
        }
        # fmt: on
        self.skip_transaction_types = []

    # def deep_identify(self, file):
    #     last_three = self.config.get("account_number", "")[-3:]
    #     # return self.column_labels_line in cache.get_file(file).head() and f"XX{last_three}" in file

    def prepare_processed_table(self, rdr):
        rdr = rdr.convert("amount", lambda i: -i)
        return rdr
