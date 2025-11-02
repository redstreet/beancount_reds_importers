IBKR importer and downloader.

### Importer

This is an IBKR importer that imports `.xml` files downloaded by using the IBKR Flex
Query system, which is a way to extensively customize your data download. IBKR lets you
specify fields to download. You might want to modify it according to your preference,
and extend the importer.

The importer itself is similar to any other reds-importer.

Multi-account support is provided via the
[multiplexer importer](https://github.com/redstreet/beancount_reds_importers/tree/main/beancount_reds_importers/importers/multiplexer).

### Downloader
It does both. Download cmd if you store your IBKR token in `pass`:

```
reds-ibkr-flexquery-download $(pass ibkr_token) 123456 > ibkr_flex_main.xml
```
where `123456` is your account number.
