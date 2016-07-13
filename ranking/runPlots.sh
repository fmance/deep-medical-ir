#!/bin/bash

echo "Diag 2014"
echo "-------------------------------------------------------------------"
python plotPrec.py --year 2014	--cat diag	--title_prefix 1-
echo

echo "Diag 2015"
echo "-------------------------------------------------------------------"
python plotPrec.py --year 2015 	--cat diag	--title_prefix 2-
echo

echo "Diag AVERAGE"
echo "-------------------------------------------------------------------"
python plotPrec.py 				--cat diag	--title_prefix 3-
echo

echo "==================================================================="

echo "Test 2014"
echo "-------------------------------------------------------------------"
python plotPrec.py --year 2014	--cat test	--title_prefix 4-
echo

echo "Test 2015"
echo "-------------------------------------------------------------------"
python plotPrec.py --year 2015 	--cat test	--title_prefix 5-
echo

echo "Test AVERAGE"
echo "-------------------------------------------------------------------"
python plotPrec.py 				--cat test	--title_prefix 6-
echo

echo "==================================================================="

echo "Treat 2014"
echo "-------------------------------------------------------------------"
python plotPrec.py --year 2014	--cat treat	--title_prefix 7-
echo

echo "Treat 2015"
echo "-------------------------------------------------------------------"
python plotPrec.py --year 2015 	--cat treat	--title_prefix 8-
echo

echo "Treat AVERAGE"
echo "-------------------------------------------------------------------"
python plotPrec.py 				--cat treat	--title_prefix 9-
echo

echo "==================================================================="

echo "All 2014"
echo "-------------------------------------------------------------------"
python plotPrec.py --year 2014 				--title_prefix 10-
echo

echo "All 2015"
echo "-------------------------------------------------------------------"
python plotPrec.py --year 2015 				--title_prefix 11-
echo

echo "All AVERAGE"
echo "-------------------------------------------------------------------"
python plotPrec.py 							--title_prefix 12-
echo

echo "==================================================================="
