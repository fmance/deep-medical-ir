#!/bin/bash

classId=$1
weightName=$2
restype=$3

for weight in `seq 0.0 0.02 1.0`
do
	p2014=`python simplererank.py $classId 2014$restype --$weightName=$weight| grep -Po "MaxP10=\K(0.\d+)"`
	p2015=`python simplererank.py $classId 2015$restype --$weightName=$weight| grep -Po "MaxP10=\K(0.\d+)"`
	echo -en $weight "\t" $p2014 $p2015 "\t"
	echo -e "scale=4;" \($p2014+$p2015\)/2 | bc -l
done
	
