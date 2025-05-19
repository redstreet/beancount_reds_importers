from os import path

from setuptools import find_packages, setup

with open(path.join(path.dirname(__file__), "README.md")) as readme:
    LONG_DESCRIPTION = readme.read()

setup(
    name="beancount_reds_importers",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="Importers for various institutions for Beancount",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/redstreet/beancount_reds_importers",
    author="Red Street",
    author_email="redstreet@users.noreply.github.com",
    keywords="importer ingestor beancount accounting",
    license="GPL-3.0",
    packages=find_packages(),
    include_package_data=True,
    extras_require={
        "dev": [
            "isort",
            "pytest",
            "ruff",
        ]
    },
    install_requires=[
        "click >= 8.1.7",
        "beangulp >= 0.2.0",
        "beancount >= 3.0.0",
        "click_aliases >= 1.0.4",
        "dateparser >= 1.2.0",
        "ofxparse >= 0.21",
        "openpyxl >= 3.1.2",
        "packaging >= 23.1",
        "pdfplumber>=0.11.0",
        "petl >= 1.7.15",
        "tabulate >= 0.9.0",
        "tqdm >= 4.66.2",
    ],
    entry_points={
        "console_scripts": [
            "ofx-summarize = beancount_reds_importers.util.ofx_summarize:summarize",
            "bean-download = beancount_reds_importers.util.bean_download:cli",
            "reds-ibkr-flexquery-download = beancount_reds_importers.importers.ibkr.flexquery_download:flexquery_download",
        ]
    },
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
)
