#!/bin/bash

beancount_main=my.beancount

echo "---------------------------------------------------------------------"
echo "Import of investment accounts (without smart-importer)"
echo "---------------------------------------------------------------------"

file=OfxDownload.qfx
./import.py identify $file
./import.py extract -e $beancount_main $file


echo "---------------------------------------------------------------------"
echo "With smart-importer"
echo "---------------------------------------------------------------------"
file=transactions.qfx
./import-smart.py identify $file
./import-smart.py extract -e $beancount_main $file

