#!/bin/bash

file=$1
beancount_main=my.beancount

bean-identify my.import $file
bean-extract my.import -f $beancount_main $file

bean-identify my-smart.import $file
bean-extract my-smart.import -f $beancount_main $file

# mkdir -pv filed
# bean-file -o filed my.import $file
