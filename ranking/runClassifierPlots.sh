#!/bin/bash

fusion=$1

declare -a classifiers=(
"SVMPerf.10.0.01"
"SVMPerf.05.0.001"
"PassiveAggressiveClassifier.hinge"
"Perceptron"
"RidgeClassifier"
"LinearSVC.squared_hinge.l2"
"SGDClassifier.log.l2"
"SGDClassifier.log.elasticnet"
"SGDClassifier.hinge.l2"
"SGDClassifier.hinge.elasticnet"
"SGDClassifier.squared_loss.l2"
"SGDClassifier.squared_loss.elasticnet"
"SGDClassifier.epsilon_insensitive.l2"
"SGDClassifier.epsilon_insensitive.elasticnet"
"Pipeline.epsilon_insensitive.l2"
#"BernoulliNB"
#"MultinomialNB"
#"NearestCentroid"
#"RandomForestClassifier"
#"SGDClassifier.squared_hinge.l2"
#"SGDClassifier.squared_hinge.elasticnet"
#"NN"
#"all"
)

function normalClassifiers {
	for classifier in ${classifiers[@]}
		do
			python plotClassifier.py --classifier $classifier --fusion $fusion
			python plotClassifier.py --classifier $classifier.hedges --fusion $fusion
			echo "----------------------------"
		done
}

function svmPerfClassifiers {
	for loss in 10 05 #04 03 02 01 00
	do
		for c in 1 0.1 0.01 0.001 0.0001
		do
#			python plotClassifier.py --classifier SVMPerf.$loss.$c --fusion $fusion
			python plotClassifier.py --classifier SVMPerf.$loss.$c.hedges --fusion $fusion
			echo "--------------------------------------"
		done
	done
}

normalClassifiers
#svmPerfClassifiers


