year=$2

java -jar trunk/bin/RankLib.jar -load model/f$1.ca -rank ../../ir/results/features-$year.txt -score scores.txt ${@:3}
echo "calling python rerank"
python rerank.py $year

echo
echo "Test"
 java -jar trunk/bin/RankLib.jar -load model/f$1.ca -test ../../ir/results/features-$year.txt -metric2T P@10 ${@:3}

echo 

echo "Trec-eval"
../../eval/trec_eval.9.0/trec_eval  ../../data/qrels/qrels-treceval-$year.txt results-reranked.txt

cd ..
python unjudged.py ../data/qrels/qrels-treceval-$year.txt supervised/results-reranked.txt
cd -
