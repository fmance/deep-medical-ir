#!/bin/bash

RESTYPE=$1
CLASSIFIER=$2

python simplererank.py diag 2014$RESTYPE --classifier $CLASSIFIER
python simplererank.py diag 2015$RESTYPE --classifier $CLASSIFIER
echo -------------------------------------
python simplererank.py test 2014$RESTYPE --classifier $CLASSIFIER
python simplererank.py test 2015$RESTYPE --classifier $CLASSIFIER
echo -------------------------------------
python simplererank.py treat 2014$RESTYPE --classifier $CLASSIFIER
python simplererank.py treat 2015$RESTYPE --classifier $CLASSIFIER
