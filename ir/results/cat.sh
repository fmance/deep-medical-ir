function catFiles() {
	target=$1
	CLASSIFIER=$2
	cat results-$target.txt.reranked.diag.$CLASSIFIER \
		results-$target.txt.reranked.test.$CLASSIFIER \
		results-$target.txt.reranked.treat.$CLASSIFIER >  results-$target.txt.reranked.$CLASSIFIER
}
TARGET=$1
CLASSIFIER=$2
catFiles $TARGET $CLASSIFIER
