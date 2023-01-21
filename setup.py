from os import path
from setuptools import find_packages, setup

with open(path.join(path.dirname(__file__), 'README.md')) as readme:
    LONG_DESCRIPTION = readme.read()

setup(
    name='beancount_reds_importers',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Importers for various institutions for Beancount',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://github.com/redstreet/beancount_reds_importers',
    author='Red Street',
    author_email='redstreet@users.noreply.github.com',
    keywords='importer ingestor beancount accounting',
    license='GPL-3.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click >= 7.0',
        'beancount >= 2.3.5',
        'click_aliases >= 1.0.1',
        'ofxparse >= 0.21',
        'openpyxl >= 3.0.9',
        'packaging >= 20.3',
        'petl >= 1.7.4',
        'tabulate >= 0.8.9',
        'tqdm >= 4.64.0',
    ],
    entry_points={
        'console_scripts': [
            'ofx-summarize = beancount_reds_importers.util.ofx_summarize:summarize',
            'bean-download = beancount_reds_importers.util.bean_download:cli',
        ]
    },
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
)
