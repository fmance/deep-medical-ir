#!/bin/bash

set -e
set -u

rm -f lambdas*.txt rerank-results-201*

classId=$1
year=$2

irResultsDir="../ir/results/"

declare -a classifiers=(
"LinearSVC.squared_hinge.l2"
"SGDClassifier.hinge.l2"
"SGDClassifier.hinge.elasticnet"
"SGDClassifier.squared_loss.l2"
"SGDClassifier.squared_loss.elasticnet"
"SGDClassifier.epsilon_insensitive.l2"
"SGDClassifier.epsilon_insensitive.elasticnet"
"Pipeline.epsilon_insensitive.l2"
)

function max {
	for classifier in ${classifiers[@]}
	do
		p10=`python simplererank.py $classifier $classId $year | grep -Po "MaxP10=\K(0.\d+)"`
		echo -e "$p10"
	done
}

function all {
	results=()
	for classifier in ${classifiers[@]}
	do
		python simplererank.py $classifier $classId $year
	done
}

max
