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
TARGET = sys.argv[2]
YEAR = TARGET[:4]

USE_HEDGES = False

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]
QUERY_RANGE = range(QUERY_OFFSET, QUERY_OFFSET + 10)

QRELS_FILE = "../data/qrels/qrels-treceval-" + YEAR + ".txt"
BASELINE_RESULTS_FILE = "../ir/results/results-" + TARGET + ".txt"
EVAL_PROGNAME = "../eval/trec_eval.9.0/trec_eval"

QRELS = utils.readQrels(QRELS_FILE)

CLASSIFIERS = [
	"Basic",
#	"LinearSVC.squared_hinge.l2", 
#	"SGDClassifier.hinge.l2",
#	"SGDClassifier.hinge.elasticnet",
#	"SGDClassifier.squared_loss.l2",
#	"SGDClassifier.squared_loss.elasticnet",
#	"SGDClassifier.epsilon_insensitive.l2",
	"SGDClassifier.epsilon_insensitive.elasticnet",
#	"Pipeline.epsilon_insensitive.l2"
]

if len(sys.argv) > 3 and sys.argv[3] != "all":
	CLASSIFIERS = [sys.argv[3]]

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
		doc, ranks, scores = zip(*(baselineResults[qid]))
		normScores[qid] = dict(zip(doc, zip(ranks, stats.zscore(scores))))
	return normScores

def getClassifierScores():
	scores = defaultdict(float)
	for classifier in CLASSIFIERS:
		for did, score in utils.readClassPredictions(classifier, CLASS_ID, USE_HEDGES).items():
			scores[did] += score
	return {did: score/len(CLASSIFIERS) for did, score in scores.items()}
#	return zscoreDictValues(scores)

def getP10(qrelsFile, resultsFile):
	output = subprocess.Popen([EVAL_PROGNAME, qrelsFile, resultsFile], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	index = output.index("P_10")
	return float(output[index + 2])

def qrelStr(rel):
	return str(rel) if rel != 0 else ""
	
def rerankScores(weight, baselineScores, classifierScores, rerankedFile):
	out = open(rerankedFile, "w")
	for qid in QUERY_RANGE:
		queryQrels = dict(QRELS[qid])
		queryScores = baselineScores[qid]
		rerankedScores = [(did, interpolate(queryScores[did][1], classifierScores.get(did), weight))
						   for did in queryScores.keys()]
		rerankedScores.sort(key = lambda docScore : docScore[1], reverse = True)
		rank = 1
		for did, score in rerankedScores:
			out.write("%d Q0 %s %d %f STANDARD\t#\t%f\t%d\t%f\t%+.2f\t\t%s\n" %
							(qid, did, rank, score,
							weight, queryScores[did][0], queryScores[did][1], classifierScores.get(did), qrelStr(queryQrels.get(did))))
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
		print "%f %f" % (weight, p10)
	
	bestWeights = [weight for (weight, p10) in allP10 if p10 == maxP10]
	print "MaxP10=%f/lambda=%f" % (maxP10, bestWeights[0]),

	rerankScores(bestWeights[0], baselineScores, classifierScores, rerankedFile)
	return maxP10, allP10

def run():
	baselineScores = getBaselineScores(BASELINE_RESULTS_FILE)
	classifierScores = getClassifierScores()
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID
 	lambdaRerank(QRELS_FILE, baselineScores, classifierScores, rerankedFile)

run()

def getRandomClassifiers(dids, num):
	classifiers = []
	for _ in range(0, num):
		classifiers.append(dict(zip(dids, np.random.choice([-1, 1], size=len(dids)))))
	return classifiers

def random(numIter):
	baselineScores = getBaselineScores(BASELINE_RESULTS_FILE)
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID + ".random"
	classifiedDids = utils.readInts(os.path.join(utils.RES_AND_QRELS_DIR, "ids.txt"))
	randomClassifiers = getRandomClassifiers(classifiedDids, numIter)
	maxP10 = 0.0
	
	for weight in np.linspace(0.2,1,41):
		sumP10 = 0.0
		for i in range(0, numIter):
			rerankScores(weight, baselineScores, randomClassifiers[i], rerankedFile)
			p10 = getP10(QRELS_FILE, rerankedFile)
			sumP10 += p10
		avgP10 = sumP10/numIter
		maxP10 = max(avgP10, maxP10)
		print round(avgP10, 3)
	print "MaxP10=%f" % maxP10
	
#random(100)



