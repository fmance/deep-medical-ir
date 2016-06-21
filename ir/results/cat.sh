target=$1

cat results-$target.txt.reranked.diag \
	results-$target.txt.reranked.test \
	results-$target.txt.reranked.treat >  results-$target.txt.reranked
