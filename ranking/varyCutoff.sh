#!/bin/bash

classId=$1
classifier=$2

for divisionCutoff in `seq 1 0.25 6`
do
	for maxCutoff in `seq 1 0.25 3`
	do
		p2014Sum=`	python simplererank.py $classId 2014-sum  	--classifier $classifier --max_cutoff $maxCutoff --division_cutoff $divisionCutoff 	| grep -Po "MaxP10=\K(0.\d+)"`
		p2015Sum=`	python simplererank.py $classId 2015-sum 	--classifier $classifier --max_cutoff $maxCutoff --division_cutoff $divisionCutoff 	| grep -Po "MaxP10=\K(0.\d+)"`
		p2014Desc=`	python simplererank.py $classId 2014-desc 	--classifier $classifier --max_cutoff $maxCutoff --division_cutoff $divisionCutoff 	| grep -Po "MaxP10=\K(0.\d+)"`
		p2015Desc=`	python simplererank.py $classId 2015-desc 	--classifier $classifier --max_cutoff $maxCutoff --division_cutoff $divisionCutoff 	| grep -Po "MaxP10=\K(0.\d+)"`
		echo -en  $divisionCutoff $maxCutoff " "
		avg=`echo -e "scale=4;" \($p2014Sum+$p2015Sum+$p2014Desc+$p2015Desc\)/4 | bc -l`
		echo -e "$avg \t#" $cutoffType $cutoff "\t" $p2014Sum $p2015Sum $p2014Desc $p2015Desc"\t"
	done
done
	
