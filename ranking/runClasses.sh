#!/bin/bash

python simplererank.py diag 2014
python simplererank.py diag 2015
echo -------------------------------------
python simplererank.py test 2014
python simplererank.py test 2015
echo -------------------------------------
python simplererank.py treat 2014
python simplererank.py treat 2015
