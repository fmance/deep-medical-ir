#!/bin/bash

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

#"PL2F"
#"BM25F"
#"ML2"
#"MDL2"
)

year=$1

topics=../data/queries/topics-$year-terrier.xml
topicsProcessed=../data/queries/topics-$year-terrier-processed.xml

evalProg=../eval/trec_eval.9.0/trec_eval
qrelFile=../data/qrels/qrels-treceval-$year.txt

terrier=terrier-core-4.1/bin/trec_terrier.sh
terrierResultsDir=terrier-core-4.1/var/results/

function run() {
	for model in "${models[@]}"
	do
	   	echo "Running model " $model
	   	echo
	   	
	   	$terrier -r 	-Dtrec.results.file=results-$year-$model.txt 				-Dtrec.topics=$topics 			-Dtrec.model=$model
#	   	$terrier -r -q 	-Dtrec.results.file=results-$year-$model-qe.txt 			-Dtrec.topics=$topics		 	-Dtrec.model=$model

#	   	$terrier -r 	-Dtrec.results.file=results-$year-$model-processed.txt 		-Dtrec.topics=$topicsProcessed 	-Dtrec.model=$model
#	   	$terrier -r -q 	-Dtrec.results.file=results-$year-$model-processed-qe.txt 	-Dtrec.topics=$topicsProcessed 	-Dtrec.model=$model
		
		echo "--------------------------------------"
		echo
	done
}

function evaluate() {
	for model in "${models[@]}"
	do
	    prec=`				$evalProg 	$qrelFile $terrierResultsDir/results-$year-$model.txt 				| grep -Po "\b(P_10\s+all\s+)\K0.\d+\b"`
#	   	precQE=`			$evalProg	$qrelFile $terrierResultsDir/results-$year-$model-qe.txt 			| grep -Po "\b(P_10\s+all\s+)\K0.\d+\b"`
#	   	
#	    precProcessed=`		$evalProg 	$qrelFile $terrierResultsDir/results-$year-$model-processed.txt 	| grep -Po "\b(P_10\s+all\s+)\K0.\d+\b"`
#	    precProcessedQE=`	$evalProg 	$qrelFile $terrierResultsDir/results-$year-$model-processed-qe.txt 	| grep -Po "\b(P_10\s+all\s+)\K0.\d+\b"`
	    
	    echo $prec #$precQE $precProcessed $precProcessedQE
	done
}

run
evaluate
 
