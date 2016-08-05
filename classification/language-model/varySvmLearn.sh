class=$1
hedges=$2

for loss in 10 05 04 03 02 01 00
do
	for c in 1 0.1 0.01 0.001 0.0001
	do
		echo $c $loss
		./svmlearn.sh $class $c $loss $hedges
		echo "--------------------------------------"
	done
done
