#!/bin/python

import os
import math
from scipy import stats
import subprocess
import numpy as np
import itertools
import sys
import pprint
from collections import defaultdict

sys.path.insert(0, "../utils/")
import utils

CLASS_ID = sys.argv[1]
YEAR = sys.argv[2]

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]
QUERY_RANGE = range(QUERY_OFFSET, QUERY_OFFSET + 10)

QRELS_FILE = "../data/qrels/qrels-treceval-" + YEAR + ".txt"
BASELINE_RESULTS_FILE = "../ir/results/results-" + YEAR + ".txt"
EVAL_PROGNAME = "../eval/trec_eval.9.0/trec_eval"

CLASSIFIERS = [
	"LinearSVC.squared_hinge.l2", 
	"SGDClassifier.hinge.l2",
	"SGDClassifier.hinge.elasticnet",
	"SGDClassifier.squared_loss.l2",
	"SGDClassifier.squared_loss.elasticnet",
	"SGDClassifier.epsilon_insensitive.l2",
	"SGDClassifier.epsilon_insensitive.elasticnet",
	"Pipeline.epsilon_insensitive.l2"
]

def interpolate(x, y, w):
	if y == None:
		return x
	else:
		return w * x + (1 - w) * y

def zscoreDictValues(d):
	return dict(zip(d.keys(), stats.zscore(d.values())))

def getBaselineScores(baselineResultsFile):
	baselineResults = utils.readResults(baselineResultsFile)
	normScores = {}
	for qid in QUERY_RANGE:
		doc, _, scores = zip(*(baselineResults[qid]))
		normScores[qid] = dict(zip(doc, stats.zscore(scores)))
	return normScores

def getClassifierScores():
	scores = defaultdict(float)
	for classifier in CLASSIFIERS:
		for did, score in utils.readClassPredictions(classifier, CLASS_ID).items():
			scores[did] += score/len(CLASSIFIERS)
	return zscoreDictValues(scores)

def getP10(qrelsFile, resultsFile):
	output = subprocess.Popen([EVAL_PROGNAME, qrelsFile, resultsFile], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	index = output.index("P_10")
	return float(output[index + 2])

def rerankScores(weight, baselineScores, classifierScores, rerankedFile):
	out = open(rerankedFile, "w")
	for qid in QUERY_RANGE:
		queryScores = baselineScores[qid]
		rerankedScores = [(did, interpolate(queryScores[did], classifierScores.get(did), weight))
						   for did in queryScores.keys()]
		rerankedScores.sort(key = lambda docScore : docScore[1], reverse = True)
		rank = 1
		for did, score in rerankedScores:
			out.write("%d Q0 %s %d %f STANDARD\n" % (qid, did, rank, score))
			rank += 1
	out.close()

def lambdaRerank(qrelsFile, baselineScores, classifierScores, rerankedFile):
	allP10 = []
	maxP10 = 0.0
	for weight in np.linspace(0.2,1,41):
		rerankScores(weight, baselineScores, classifierScores, rerankedFile)
		p10 = getP10(qrelsFile, rerankedFile)
		maxP10 = max(p10, maxP10)
		allP10.append((weight, p10))
		print "%f" % p10
	
	bestWeights = [weight for (weight, p10) in allP10 if p10 == maxP10]
	print "MaxP10=%f" % maxP10,

	rerankScores(bestWeights[0], baselineScores, classifierScores, rerankedFile)
	return maxP10, allP10

def run():
	baselineScores = getBaselineScores(BASELINE_RESULTS_FILE)
	classifierScores = getClassifierScores()
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID
 	lambdaRerank(QRELS_FILE, baselineScores, classifierScores, rerankedFile)

run()

#def random(weight):
#	s=0.0
#	for i in range(1,101):
#		global class_predictions
#		class_predictions = utils.readclassifierScores(classifier, CLASS_ID)
#		class_predictions = zscore_dict(class_predictions)
#	
#	#	getBestWeights("P10", qrelsTrecEval, qrelsSampleEval, baselineNormScores, rerankedFile+".random")
#		simple_rerank(weight, baselineNormScores, rerankedFile+".random")
#		p10 = get_precision_at("10", qrelsTrecEval, rerankedFile+".random")
#		s+=p10
#		print "%f %f" % (p10, s/i)


#lambdaRerank("P10")
#random(0.75)


