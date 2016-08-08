#!/bin/bash

RESTYPE=$1
CLASSIFIER=$2
FUSION=$3

python simplererank.py diag 2014$RESTYPE --classifier $CLASSIFIER --fusion $FUSION
python simplererank.py diag 2015$RESTYPE --classifier $CLASSIFIER --fusion $FUSION
echo -------------------------------------
python simplererank.py test 2014$RESTYPE --classifier $CLASSIFIER --fusion $FUSION
python simplererank.py test 2015$RESTYPE --classifier $CLASSIFIER --fusion $FUSION
echo -------------------------------------
python simplererank.py treat 2014$RESTYPE --classifier $CLASSIFIER --fusion $FUSION
python simplererank.py treat 2015$RESTYPE --classifier $CLASSIFIER --fusion $FUSION
