java -jar trunk/bin/RankLib.jar -load model/f$1.ca -rank ../../ir/results/features-2015.txt -score scores.txt ${@:3}
echo "calling python rerank"
python rerank.py 2015

echo
echo "Test"
 java -jar trunk/bin/RankLib.jar -load model/f$1.ca -test ../../ir/results/features-2015.txt -metric2T P@10 ${@:3}

echo 

echo "Trec-eval"
../../eval/trec_eval.9.0/trec_eval  ../../data/qrels/qrels-treceval-2015.txt results-reranked.txt

cd ..
python unjudged.py ../data/qrels/qrels-treceval-2015.txt supervised/results-reranked.txt
cd -
