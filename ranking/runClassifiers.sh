#!/bin/bash

set -e
set -u

rm -f lambdas*.txt rerank-results-201*

classId=$1
year=$2

irResultsDir="../ir/results/"

declare -a classifiers=(
"Basic"
"BernoulliNB"
"MultinomialNB"
"NearestCentroid"
"PassiveAggressiveClassifier.hinge"
"Perceptron"
"RidgeClassifier"
"RandomForestClassifier"
"LinearSVC.squared_hinge.l2"
"SGDClassifier.log.l2"
"SGDClassifier.log.elasticnet"
"SGDClassifier.hinge.l2"
"SGDClassifier.hinge.elasticnet"
"SGDClassifier.squared_hinge.l2"
"SGDClassifier.squared_hinge.elasticnet"
"SGDClassifier.squared_loss.l2"
"SGDClassifier.squared_loss.elasticnet"
"SGDClassifier.epsilon_insensitive.l2"
"SGDClassifier.epsilon_insensitive.elasticnet"
"Pipeline.epsilon_insensitive.l2"
"NN"
"all"
)

function max {
	for classifier in ${classifiers[@]}
	do
		p10=`python simplererank.py $classId $year --classifier $classifier | grep -Po "MaxP10=\K(0.\d+)"`
		printf "%-40s\t%s\n" $classifier $p10
	done
}

function all {
	results=()
	for classifier in ${classifiers[@]}
	do
		python simplererank.py $classId $year --classifier $classifier
	done
}

max
