#!/bin/bash

RESTYPE=$1

python simplererank.py diag 2014$RESTYPE
python simplererank.py diag 2015$RESTYPE
echo -------------------------------------
python simplererank.py test 2014$RESTYPE
python simplererank.py test 2015$RESTYPE
echo -------------------------------------
python simplererank.py treat 2014$RESTYPE
python simplererank.py treat 2015$RESTYPE
