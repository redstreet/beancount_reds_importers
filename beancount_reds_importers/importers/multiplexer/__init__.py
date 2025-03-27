from beangulp import importer

class Importer(importer.Importer):
    """Multiplexer Importer: used when multiple accounts exist in a single input file, which is
    typical of ofx/qfx files.

    This is a quick and dirty version. Note that picks the first importer's account, filename etc.,
    if not specified in the multiplexer config. Example instantiation, assuming multiple vanguard
    accounts with different account numbers are all expected to be contained in a single ofx file:

    ```
    #!/usr/bin/env python3
    CONFIG = [multiplexer.Importer({
        'importers': [
            vanguard.Importer({'account_number': 123, ...}),
            vanguard.Importer({'account_number': 456, ...}),
            vanguard.Importer({'account_number': 789, ...}),
        ]
    })]

    if __name__ == "__main__":
        ingest = beangulp.Ingest(CONFIG)
        ingest()
    ```

    """

    def __init__(self, config):
        self.config = config
        self.applicable_importers = None

    def get_applicable_importers(self, filepath):
        """Return a list of importers that identify the file as applicable."""

        if self.applicable_importers:
            return self.applicable_importers # Preserve previously build importer instantiations

        applicable = []
        for imp in self.config.get("importers", []):
            try:
                if imp.identify(filepath):
                    applicable.append(imp)
            except Exception:
                # Optionally log or handle exceptions from an importer
                continue
        self.applicable_importers = applicable
        return applicable

    def identify(self, filepath):
        """The multiplexer identifies the file if any underlying importer does."""

        # Without this, if there are multiple multiplexer importers in one's CONFIG list passed to
        # beangulp, then all previous ones that were instantiated will return True for all
        # subsequent calls
        self.applicable_importers = None

        return bool(self.get_applicable_importers(filepath))

    def account(self, filepath):
        """If one or more importers apply, delegate to the first one."""

        if self.config.get('account', None):
            return self.config['account']

        applicable = self.get_applicable_importers(filepath)
        if applicable:
            return applicable[0].account(filepath)
        return "Assets:Uninitialized"

    def date(self, filepath):
        imps = self.get_applicable_importers(filepath)
        return max((d for d in (imp.date(filepath) for imp in imps) if d), default=None)

    def filename(self, filepath):
        if self.config.get('filename', None):
            return self.config['filename']

        # Delegate filename determination to the first applicable importer.
        applicable = self.get_applicable_importers(filepath)
        if applicable:
            return applicable[0].filename(filepath)
        return None

    def extract(self, filepath, existing=None):
        # Run extract on all applicable importers and merge their outputs.
        extracted = []
        for imp in self.get_applicable_importers(filepath):
            extracted += imp.extract(filepath, existing)
        return extracted
