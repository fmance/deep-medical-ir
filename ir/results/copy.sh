#!/bin/bash

function copyYear() {
	year=$1
	resFile=results-$year
	cp models/results-$year-BM25_Lucene.txt $resFile.txt
	head -n 1000 		$resFile.txt > $resFile-diag.txt
	sed -n '1001,2000p' $resFile.txt > $resFile-test.txt
	tail -n 1000 		$resFile.txt > $resFile-treat.txt
}

copyYear 2014
copyYear 2015

