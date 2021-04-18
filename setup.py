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
    url='https://github.com/redstreet/beancount_reds_ingestor',
    author='Red Street',
    author_email='redstreet@users.noreply.github.com',
    keywords='importer ingestor beancount accounting',
    license='GPL-3.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'beancount>=2.2.3',
        'ofxparse>=0.20',
        'petl>=1.7.2',
    ],
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
)
