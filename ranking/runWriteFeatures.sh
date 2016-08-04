set -e

for classId in diag test treat
do
	for year in 2014 2015
	do
		for target in sum desc
		do
			python writefeatures.py $classId $year-$target $1
		done
	done
done

echo
echo
echo "!!!!!!!!!!!!!!!!!!!!!!!!"
echo "Run ./catFeatures !!!"
echo "!!!!!!!!!!!!!!!!!!!!!!!!"
echo
echo
