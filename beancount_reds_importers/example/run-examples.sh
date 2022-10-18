#!/bin/bash

file=OfxDownload.qfx
./import.py identify OfxDownload.qfx
./import.py extract -e my.beancount OfxDownload.qfx


# ./smart-import.py identify $file
# ./smart-import.py extract -e $beancount_main $file

# mkdir -pv filed
# bean-file -o filed my.import $file
