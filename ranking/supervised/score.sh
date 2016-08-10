set -e

target=$2 # CLASSID-YEAR-SUM/DESC-CLASSIFIER
year=${target//[A-Za-z\-]/}
year=${year:0:4}
rerankerConfig=$3
rerankedResultsFile="results-"$target-test"."$rerankerConfig".reranked.txt"

java -jar trunk/bin/RankLib.jar -load model/f$1.ca -rank ../../ir/results/features-$target-test.txt -score scores.txt ${@:4}

echo "calling python rerank"
python rerank.py $target-test $rerankerConfig

echo "-----------------------------------"
echo "Test"
 java -jar trunk/bin/RankLib.jar -load model/f$1.ca -test ../../ir/results/features-$target-test.txt -metric2T P@10 ${@:4}

echo "-----------------------------------"

echo "Trec-eval"
../../eval/trec_eval.9.0/trec_eval  ../../data/qrels/qrels-treceval-$year.txt $rerankedResultsFile

echo "-----------------------------------"
echo "Unjudged"

cd ..
python unjudged.py ../data/qrels/qrels-treceval-$year.txt supervised/$rerankedResultsFile
cd -
