target=$2 # CLASSID-YEAR-SUM/DESC
year=${target//[A-Za-z\-]/}

java -jar trunk/bin/RankLib.jar -load model/f$1.ca -rank ../../ir/results/features-$target-test.txt -score scores.txt ${@:3}

echo "calling python rerank"
python rerank.py $target-test

echo "-----------------------------------"
echo "Test"
 java -jar trunk/bin/RankLib.jar -load model/f$1.ca -test ../../ir/results/features-$target-test.txt -metric2T P@10 ${@:3}

echo "-----------------------------------"

echo "Trec-eval"
../../eval/trec_eval.9.0/trec_eval  ../../data/qrels/qrels-treceval-$year.txt results-reranked.txt

echo "-----------------------------------"
echo "Unjudged"

cd ..
python unjudged.py ../data/qrels/qrels-treceval-$year.txt supervised/results-reranked.txt
cd -
