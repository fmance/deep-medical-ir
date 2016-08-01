#!/bin/bash

fusion=$1

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
"SVMPerf"
"NN"
"all"

"BernoulliNB.hedges"
"MultinomialNB.hedges"
"NearestCentroid.hedges"
"PassiveAggressiveClassifier.hinge.hedges"
"Perceptron.hedges"
"RidgeClassifier.hedges"
"RandomForestClassifier.hedges"
"LinearSVC.squared_hinge.l2.hedges"
"SGDClassifier.log.l2.hedges"
"SGDClassifier.log.elasticnet.hedges"
"SGDClassifier.hinge.l2.hedges"
"SGDClassifier.hinge.elasticnet.hedges"
"SGDClassifier.squared_hinge.l2.hedges"
"SGDClassifier.squared_hinge.elasticnet.hedges"
"SGDClassifier.squared_loss.l2.hedges"
"SGDClassifier.squared_loss.elasticnet.hedges"
"SGDClassifier.epsilon_insensitive.l2.hedges"
"SGDClassifier.epsilon_insensitive.elasticnet.hedges"
"Pipeline.epsilon_insensitive.l2.hedges"
"SVMPerf.hedges"

)

function normalClassifiers {
	for classifier in ${classifiers[@]}
		do
			python plotClassifier.py --classifier $classifier --fusion $fusion
			echo "----------------------------"
		done
}

function svmPerfClassifiers {
	for loss in 10 05 04 03 02 01 00
	do
		for c in 0.0001 0.001 0.01 0.1 1
		do
#			python plotClassifier.py --classifier SVMPerf.$loss.$c --fusion $fusion
			python plotClassifier.py --classifier SVMPerf.$loss.$c.hedges --fusion $fusion
			echo "--------------------------------------"
		done
	done
}

svmPerfClassifiers


