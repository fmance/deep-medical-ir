set -e

trainOrTest=$1
clf=$2

for classId in diag test treat
do
	for year in 2014 2015 2016
	do
		for target in sum desc
		do
			python writefeatures.py $classId $year-$target $trainOrTest --classifier $clf
		done
	done
done

for classId in diag test treat
do
	python writefeatures.py $classId 2016-note $trainOrTest --classifier $clf
done

echo
echo
echo "!!!!!!!!!!!!!!!!!!!!!!!!"
echo "Run ./catFeatures !!!"
echo "!!!!!!!!!!!!!!!!!!!!!!!!"
echo
echo
