#!/bin/bash

set -e
set -u

rm -f lambdas*.txt rerank-results-201*

classifier=$1

irResultsDir="../ir/results/"

declare -a models=(
#"BB2"
#"BM25"
#"DFR_BM25"
#"DLH"
#"DLH13"
#"DPH"
#"DFRee"
#"Hiemstra_LM"
#"In_expB2"
#"In_expC2"
#"InL2"
#"LemurTF_IDF"
#"LGD"
#"PL2"
#"TF_IDF"
"BM25_Lucene"

#"PL2F"
#"BM25F"
#"ML2"
#"MDL2"
)

evalProg=../eval/trec_eval.9.0/trec_eval

function rerank() {
	model=$1
	year=$2
	cp $irResultsDir/models/results-$year-$model.txt $irResultsDir/results-$year.txt
	cd $irResultsDir; ./split.sh $year; cd -
	lambdaDiag=`	python simplererank.py $classifier $year diag 	| grep -Po "Weights=\K.*"`
	lambdaTest=`	python simplererank.py $classifier $year test	| grep -Po "Weights=\K.*"`
	lambdaTreat=`	python simplererank.py $classifier $year treat	| grep -Po "Weights=\K.*"`
	cd $irResultsDir; ./cat.sh $year $classifier; cd -
	echo $lambdaDiag $lambdaTest $lambdaTreat | tee -a lambdas-$year.txt
}

function evalReranked() {
	year=$1
	qrels=../data/qrels/qrels-treceval-$year.txt
	baselineResults=$irResultsDir/results-$year.txt 
	rerankedResults=$irResultsDir/results-$year.txt.reranked.$classifier
	
	precBaseline=`		$evalProg $qrels $baselineResults	| grep -Po "\b(P_10\s+all\s+)\K0.\d+\b"`
	precReranked=`		$evalProg $qrels $rerankedResults 	| grep -Po "\b(P_10\s+all\s+)\K0.\d+\b"`
	unjudgedBaseline=`	python unjudged.py $qrels $baselineResults	| grep -Po "unjudged=\K0.\d+"`
	unjudgedReranked=`	python unjudged.py $qrels $rerankedResults	| grep -Po "unjudged=\K0.\d+"`
	
	improvement=`echo $precReranked-$precBaseline|bc -l`
	
	echo $precBaseline $precReranked $improvement $unjudgedBaseline $unjudgedReranked | tee -a rerank-results-$year.txt
}

function rerankAndEvaluate() {
	year=$1
	for model in "${models[@]}"
	do
		echo "Model" $model
		rerank $model $year
		evalReranked $year
	done
}

rerankAndEvaluate 2014
rerankAndEvaluate 2015
