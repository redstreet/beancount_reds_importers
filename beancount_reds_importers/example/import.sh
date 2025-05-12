#!/bin/bash

file=$1
beancount_main=my.beancount

python _config.py identify $file
python _config.py extract -e $beancount_main $file

python _config-smart.py identify $file
python _config-smart.py extract -e $beancount_main $file

# mkdir -pv filed
# bean-file -o filed my.import $file
