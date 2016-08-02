set -x

TARGET=$1

python simplererank.py diag $TARGET
python simplererank.py test $TARGET
python simplererank.py treat $TARGET
cd ../ir/results
./cat2016.sh $TARGET
cd -

