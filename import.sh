#!/bin/bash

# this file is not tested and is provided as an example

file=$1
beancount_main=my.beancount

bean-identify my.import $file
bean-extract my.import $file
bean-extract my.import -f $beancount_main $file
bean-file -o filed my.import $file
