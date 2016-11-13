clf=$1 # e.g. SVMPerf.04.0.001.hedges

set -e
set -x

for year in 2014 2015 2016
do
	for type in sum desc
	do
		for class in diag test treat
		do
			python simplererank.py $class $year-$type --classifier $clf
		done
	done
done

for class in diag test treat
do
	python simplererank.py $class 2016-note --classifier $clf
done

#CAT

cd ../ir/results

for year in 2014 2015 2016
do
	for type in sum desc
	do
		./cat.sh $year-$type $clf.interpolation
	done
done

./cat.sh 2016-note $clf.interpolation

cd -
