#!/bin/bash

set -e
set -u

CLASS=$1
YEAR=$2

for minTerms in $(seq 50)
do
	cd ../classification/language-model > /dev/null
	python basic.py $CLASS $minTerms
	cd - > /dev/null
	python simplererank.py $CLASS $YEAR Basic
done
	
