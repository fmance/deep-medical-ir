#!/bin/bash

set -e
set -o xtrace
set -u

rm -f lambdas.txt rerank-results-201*

terrierResultsDir="../terrier/terrier-core-4.1/var/results/"
irResultsDir="../ir/results/"

declare -a models=(
"BB2"
"BM25"
"DFR_BM25"
"DLH"
"DLH13"
"DPH"
"DFRee"
"Hiemstra_LM"
"IFB2"
"In_expB2"
"In_expC2"
"InL2"
"LemurTF_IDF"
"LGD"
"PL2"
"TF_IDF"
"BM25_Lucene"

#"PL2F"
#"BM25F"
#"ML2"
#"MDL2"
)

evalProg=../eval/trec_eval.9.0/trec_eval

function rerank() {
	cp $terrierResultsDir/results-2014-$1.txt $irResultsDir/results-2014.txt
	cp $terrierResultsDir/results-2015-$1.txt $irResultsDir/results-2015.txt
	cd $irResultsDir; ./split.sh; cd -
	lambdaDiag=`	python simplererank.py NN diag 	| grep -Po "BestWeight=\K(0|1).\d+"`
	lambdaTest=`	python simplererank.py NN test	| grep -Po "BestWeight=\K(0|1).\d+"`
	lambdaTreat=`	python simplererank.py NN treat	| grep -Po "BestWeight=\K(0|1).\d+"`
	cd $irResultsDir; ./cat.sh NN; cd -
	echo $lambdaDiag $lambdaTest $lambdaTreat >> lambdas.txt
}

function evalReranked() {
	year=$1
	qrels=../data/qrels/qrels-treceval-$year.txt
	baselineResults=$irResultsDir/results-$year.txt 
	rerankedResults=$irResultsDir/results-$year.txt.reranked.NN
	
	precBaseline=`		$evalProg $qrels $baselineResults	| grep -Po "\b(P_10\s+all\s+)\K0.\d+\b"`
	precReranked=`		$evalProg $qrels $rerankedResults 	| grep -Po "\b(P_10\s+all\s+)\K0.\d+\b"`
	unjudgedBaseline=`	python unjudged.py $qrels $baselineResults	| grep -Po "unjudged=\K\d+"`
	unjudgedReranked=`	python unjudged.py $qrels $rerankedResults	| grep -Po "unjudged=\K\d+"`
	
	echo $precBaseline $precReranked $unjudgedBaseline $unjudgedReranked >> rerank-results-$year.txt
}

function rerankAndEvaluate() {
	for model in "${models[@]}"
	do
		rerank $model
		evalReranked 2014
		evalReranked 2015
	done
}

function evaluateBestAvgWeight() {
	for model in "${models[@]}"
	do
		cp $terrierResultsDir/results-2014-$model.txt $irResultsDir/results-2014.txt
		cp $terrierResultsDir/results-2015-$model.txt $irResultsDir/results-2015.txt
		cd $irResultsDir; ./split.sh; cd -
		python simplererank.py NN diag
		python simplererank.py NN test
		python simplererank.py NN treat
		cd $irResultsDir; ./cat.sh NN; cd -
		evalReranked 2014
		evalReranked 2015
	done
}

rerankAndEvaluate
#evaluateBestAvgWeight
