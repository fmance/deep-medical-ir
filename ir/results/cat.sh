classifier=$1

function catYear {
	year=$1
	cat results-$year-diag.txt.reranked.$classifier \
		results-$year-test.txt.reranked.$classifier \
		results-$year-treat.txt.reranked.$classifier >  results-$year.txt.reranked.$classifier
}

catYear 2014
catYear 2015
