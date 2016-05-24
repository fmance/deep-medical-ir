java -jar trunk/bin/RankLib.jar -load $1 -rank ../../ir/results/features-$2.txt -score scores.txt -gmax 2 ${@:3}
echo "calling python rerank"
python rerank.py $2

echo
echo "Test"
 java -jar trunk/bin/RankLib.jar -load $1 -test ../../ir/results/features-$2.txt -metric2T P@10 -gmax 2 ${@:3}

echo 

echo "Trec-eval"
../../eval/trec_eval.9.0/trec_eval  ../../data/qrels/qrels-treceval-$2.txt results-reranked.txt
