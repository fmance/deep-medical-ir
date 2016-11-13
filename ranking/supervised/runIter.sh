set -e

ranker=$1
clf=$2
trainType=$3 # sum, desc
 
function getP10() {
	p10=`./iter.sh $ranker $1 $2 ${@:3} | grep -Po "P_10\s+all\s+\K(0.\d+)"`
	echo "$p10 * 100" | bc -l
}

sum2014=`getP10 2015+2016-$trainType-$clf 2014-sum-$clf ${@:4}`
echo -n $sum2014,

desc2014=`getP10 2015+2016-$trainType-$clf 2014-desc-$clf ${@:4}`
echo -n $desc2014,

sum2015=`getP10 2014+2016-$trainType-$clf 2015-sum-$clf ${@:4}`
echo -n $sum2015,

desc2015=`getP10 2014+2016-$trainType-$clf 2015-desc-$clf ${@:4}`
echo -n $desc2015,

sum2016=`getP10 2014+2015-$trainType-$clf 2016-sum-$clf ${@:4}`
echo -n $sum2016,

desc2016=`getP10 2014+2015-$trainType-$clf 2016-desc-$clf ${@:4}`
echo -n $desc2016,

note2016=`getP10 2014+2015-$trainType-$clf 2016-note-$clf ${@:4}`
echo $note2016

printf %.2f $(echo "($sum2014+$desc2014+$sum2015+$desc2015+$sum2016+$desc2016+$note2016)/7.0" | bc -l)
echo
