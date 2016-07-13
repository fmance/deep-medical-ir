#!/bin/bash

classId=$1

for cutoff in `seq 1 0.25 20`
do
	python basic.py $classId $cutoff
	cd ../../ranking
	p2014=`python simplererank.py $classId 2014 | grep -Po "MaxP10=\K(0.\d+)"`
	p2015=`python simplererank.py $classId 2015 | grep -Po "MaxP10=\K(0.\d+)"`
	echo -en $cutoff "\t" $p2014 $p2015 "\t"
	echo -e "scale=4;" \($p2014+$p2015\)/2 | bc -l
	cd - > /dev/null
done
	
