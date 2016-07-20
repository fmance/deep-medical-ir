function catYear() {
	target=$1
	cat results-$target.txt.reranked.diag \
		results-$target.txt.reranked.test \
		results-$target.txt.reranked.treat >  results-$target.txt.reranked
}

catYear 2014$1
catYear 2015$1

