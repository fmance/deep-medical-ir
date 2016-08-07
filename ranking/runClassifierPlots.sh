#!/bin/bash

fusion=$1

declare -a classifiers=(
"SVMPerf.10.0.001"
"SVMPerf.05.0.001"
"SVMPerf.04.0.001"
"SVMPerf.02.1"
"SVMPerf.01.1"
"SVMPerf.00.0.01"

"LinearSVC.hinge.l2.0.001"
"LinearSVC.squared_hinge.l2.0.001"

"SGDClassifier.epsilon_insensitive.elasticnet"
"SGDClassifier.squared_loss.elasticnet"

"LogisticRegression.l2.0.01"

"RidgeClassifier"
"PassiveAggressiveClassifier.hinge.0.01"

"Perceptron.elasticnet"
"MultinomialNB"
)

function normalClassifiers {
	for classifier in ${classifiers[@]}
		do
#			python plotClassifier.py --classifier $classifier --fusion $fusion
			python plotClassifier.py --classifier $classifier.hedges --fusion $fusion
			echo "----------------------------"
		done
}

function svmPerfClassifiers {
	for loss in 10 05 04 03 02 01 00
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


