# Amazon GDPR Download Importers

This directory provides [Beancount Reds Importers](https://github.com/redstreet/beancount_reds_importers) for
processing your **Amazon GDPR data export**.

## What is Amazon GDPR Data?

Amazon allows you to request a full download of your order history to comply with GDPR regulations.

* You can make this request via the Amazon Privacy portal ([US](https://www.amazon.com/gp/privacycentral/dsar/preview.html) and EU sites available).
* The download is provided as a **ZIP file** containing many **CSV files** (among other data).


This importer is designed to detect those GDPR ZIP archives, extract the CSVs, and run specialized sub-importers on them.

## Supported Importers

Currently, two importers are included:

### 1. **Order History Importer**

* Processes your order history CSV.
* Each order is categorized into an **Expenses:** account.
* This importer leverages the **Smart Importer**, so accounts should be categorized accordingly.
* Example: groceries, books, electronics, etc.

### 2. **Returns Importer**

* Processes your return history CSV.
* The returns file contains **order numbers**, but not descriptions.
* Right now, returns are booked to a fixed **target account** you configure (e.g., `Assets:Amazon:Returns`).
* In the future, this importer will **join with the orders CSV** to add descriptions and richer context.

## Design Notes

* The importer automatically unpacks GDPR ZIP files and routes CSVs to the appropriate importer.
* For orders, the importer **hard-codes the Smart Importer** to ensure categorization into the correct expenses accounts.
* For returns, description lookup is not yet implemented. This will be added in a later version when CSV joins are supported.

## Usage

To be added to your list of beangulp importers:

```python
# Example ingest script snippet
from beancount_reds_importers.importers import amazongdpr
amazongdpr.AmazonGDPRZipImporter({
    'account_purchases': "Assets:Zero-Sum-Accounts:Amazon:Purchases",
    'account_returns':   "Assets:Zero-Sum-Accounts:Amazon:Returns",
    'account_returns_other': "Assets:Zero-Sum-Accounts:Returns-and-Temporary",
}),
```

* Place your GDPR ZIP(s) in your ingest folder.
* Run Beangulp as usual, and the importers will detect and process the relevant CSVs.

## Roadmap

* [ ] Remove smart importer hardcoding
* [ ] Join **returns** with **orders** to recover descriptions.
* [ ] Add support for additional Amazon GDPR CSVs (e.g., seller account, payments).
* [ ] More flexible account mapping and configuration.

## Workflow Example - Orders

A typical flow looks like this:

### Step 1. Credit Card Transaction

Your credit card transaction is first imported into a **Zero-Sum Account**.
The [smart\_importer](https://github.com/beancount/smart_importer) does this automatically:

```beancount
2022-09-02 * "AMZN Mktp US*1FASU238B"
  Liabilities:Credit-Cards:MyCard             -18.92 USD
  Assets:Zero-Sum-Accounts:Amazon:Purchases
```

### Step 2. Amazon Order

The Amazon GDPR order importer matches the order to the zero-sum account.
Here, the description comes from the **Order History CSV**:

```beancount
2022-09-03 * "Cool Stealth Canoe, Black"
  card: "Gift Certificate/Card and Visa - 1234"
  Assets:Zero-Sum-Accounts:Amazon:Purchases   -18.92 USD
  Expenses:Outdoor-Activities:Equipment
```

* If smart\_importer recognizes a pattern, it automatically categorizes to the correct expense account.
* If not, you’ll book it manually once, and smart\_importer will learn from that going forward.

### Step 3. Balancing

In most cases, the transactions in the Zero-Sum Account will **net to zero**, and you are done!

Optionally, if you use the `zero_sum` plugin, it will automatically match
transactions in memory, which helps detect any unmatched or leftover
transactions.

## Workflow Example - Returns

Returns are imported from the **Returns History CSV**. Unlike orders, the
return CSV does not contain product descriptions. For now, each return is
booked into a fixed **target account** you configure (e.g.,
`Assets:Amazon:Returns`):

### Step 1. Credit Card Transaction

Your credit card transaction is first imported into a **Zero-Sum Account**. The
[smart\_importer](https://github.com/beancount/smart_importer) does this
automatically for the most part. Returns are credits while orders are debits:

```beancount
2022-09-02 * "AMZN Mktp US*1FASU238B"
  Liabilities:Credit-Cards:MyCard             -18.92 USD
  Assets:Zero-Sum-Accounts:Amazon:Returns
```

### Step 2. Return Transaction

```beancount
2022-09-10 * "Return for Order 111-3961666-5760248"
  Assets:Zero-Sum-Accounts:Amazon:Purchases    18.92 USD
  Assets:Amazon:Returns
```

* The amount matches the order, but no description is available.
* In the future, the return importer will join against the Orders CSV to pull in product details.

# Amazon Gift Card Screenscraper Importer

This is a simple importer to import gift card transactions, screen scraped from Amazon.
See `amazon_giftcard.py` for documentation on this.
