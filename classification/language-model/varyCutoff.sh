#!/bin/bash

classId=$1
cutoffType=$2
classifier=$3

for cutoff in `seq 1 0.25 20`
do
	python basic.py $classId $cutoffType $cutoff
	cd ../../ranking
	p2014Sum=`python simplererank.py $classId 2014-sum  --classifier $classifier | grep -Po "MaxP10=\K(0.\d+)"`
	p2015Sum=`python simplererank.py $classId 2015-sum --classifier $classifier | grep -Po "MaxP10=\K(0.\d+)"`
	p2014Desc=`python simplererank.py $classId 2014-desc --classifier $classifier | grep -Po "MaxP10=\K(0.\d+)"`
	p2015Desc=`python simplererank.py $classId 2015-desc --classifier $classifier | grep -Po "MaxP10=\K(0.\d+)"`
	echo -en $cutoffType $cutoff "\t" $p2014Sum $p2015Sum $p2014Desc $p2015Desc"\t"
	echo -e "scale=4;" \($p2014Sum+$p2015Sum+$p2014Desc+$p2015Desc\)/4 | bc -l
	cd - > /dev/null
done
	
