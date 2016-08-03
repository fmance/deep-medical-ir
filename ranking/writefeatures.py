#!/usr/bin/python

import os
import math
from scipy import stats
import subprocess
import numpy as np
import itertools
import sys
import pprint
from collections import defaultdict
from optparse import OptionParser

sys.path.insert(0, "../utils/")
import utils

CLASS_ID = sys.argv[1]
TARGET = sys.argv[2]
YEAR = TARGET[:4]

if sys.argv[3] == "train":
	TRAIN = True
elif sys.argv[3] == "test":
	TRAIN = False
else:
	print "ERROR : need train or test as arg 3"
	sys.exit(0)

op = OptionParser()
op.add_option("--classifier",
			  action="store", default="SVMPerf.10.0.01.hedges",
			  help="classifier.")

(opts, args) = op.parse_args()

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]
QUERY_RANGE = range(QUERY_OFFSET, QUERY_OFFSET + 10)

QRELS_FILE = "../data/qrels/qrels-treceval-" + YEAR + ".txt"

if TRAIN:
	BASELINE_RESULTS_FILE = "../ir/results/bm25-" + TARGET.replace("-unexpanded", "") + ".txt"
	FEATURE_FILE = "../ir/results/features-" + CLASS_ID + "-" + TARGET + "-train.txt"
else:
	BASELINE_RESULTS_FILE = "../ir/results/results-" + TARGET.replace("-unexpanded", "") + ".txt"
	FEATURE_FILE = "../ir/results/features-" + CLASS_ID + "-" + TARGET + "-test.txt"
	
QRELS = utils.readQrels(QRELS_FILE)

if "." in opts.classifier:
	CLASSIFFIER_ROOT = opts.classifier[:opts.classifier.index(".")]
else:
	CLASSIFFIER_ROOT = opts.classifier

DIVISION_CUTOFFS = {"SVMPerf" : 4.0,
					"SGDClassifier": 4.0, # 8 ok
					"LinearSVC" : 6.0, # 4,8 also ok
					"NN": 4.0,
					"PassiveAggressiveClassifier": 6.0,
					"Perceptron": 8.0,
					"RidgeClassifier": 6.0,
					"Pipeline": 6.0,
					"all": 4.0}
DIVISION_CUTOFF = DIVISION_CUTOFFS.get(CLASSIFFIER_ROOT, 4.0)

MAX_CUTOFFS = {"SVMPerf" : 1.0,
			   "SGDClassifier":1.0,
			   "LinearSVC" : 1.0,
			   "NN": 1.0}
MAX_CUTOFF = MAX_CUTOFFS.get(CLASSIFFIER_ROOT, 1.0)

BASIC_WEIGHTS = {"SVMPerf": 0.1,
				 "SGDClassifier": 0.5,
				 "LinearSVC" : 0.5,
				 "NN": 0.0,
				 "PassiveAggressiveClassifier": 0.5,
				 "Perceptron": 0.5,
				 "RidgeClassifier": 0.5,
				 "Pipeline": 0.5,
				 "all": 0.1}
BASIC_WEIGHT = BASIC_WEIGHTS.get(CLASSIFFIER_ROOT, 0.0)


BAD_TRAINING_QUERIES = {"2014-sum": {17, 25}, # 0% prec: 17, 25; 10%: 3, 6, 10, 11, 13, 18, 19, 23, 29
						"2014-desc": {3, 5, 12, 13, 18, 23, 29}, # 0% prec: 3, 5, 12, 13, 18, 23, 29;  10%: 1, 6, 17, 19, 25
						"2015-sum": {5, 18, 20, 24, 25, 27}, # 0% prec: 5, 18, 20, 24, 25, 27; 10%: 2, 12, 28
						"2015-desc" : {5, 18, 20, 24, 25, 27} # 0% prec: 5, 18, 20, 24, 25, 27; 10%: 7, 9, 10, 12
					}

def getBaselineScores(baselineResultsFile):
	baselineResults = utils.readResults(baselineResultsFile)
	normScores = {}
	for qid in QUERY_RANGE:
		print "Reading baseline scores for query %d" % qid
		docs, ranks, scores = zip(*(baselineResults[qid]))
		normScores[qid] = dict(zip(docs, utils.minMaxNormalizeList(scores)))
	return normScores

def combineScores(basic, sgd):
	w = BASIC_WEIGHT #opts.sgd_weight
#	if CLASS_ID == "test":
#		sgd /= 2.0
	return (1-w) * sgd + w * basic

def getClassifierScores(baselineScores, maxCutoff, divisionCutoff):
	clfScores = utils.readClassPredictions(opts.classifier, CLASS_ID, True, False)
	
	docs, scores = clfScores.keys(), clfScores.values()
	return dict(zip(docs, utils.minMaxNormalizeList(scores)))
	
#	basicScores = utils.readClassPredictions("Basic", CLASS_ID, False, False)
#	basicScores = {did: min(maxCutoff, float(score)/divisionCutoff) for did, score in basicScores.items()}

#	finalScoresDict = {}
#	for qid, docScoresDict in baselineScores.items():
#		docs = docScoresDict.keys()
#		
#		queryBasicScores = [basicScores[did] for did in docs]
#		queryBasicScores = utils.maxNormalize(queryBasicScores) # TODO ? minmaxnormalize ?
#		
#		queryClfScores = utils.minMaxNormalizeList([clfScores[did] for did in docs])
#		
##		combinedScores = map(lambda (x,y) : BASIC_WEIGHT/(60+x) +  (1-BASIC_WEIGHT)/(60+y),
##									zip(rankList(queryBasicScores), rankList(queryClfScores)))
#		combinedScores = map(combineScores, queryBasicScores, queryClfScores)
#		if CLASS_ID == "test":
#			combinedScores = [score/2.0 for score in combinedScores]
#		
#		finalScoresDict[qid] = dict(zip(docs, zip(combinedScores, queryClfScores, queryBasicScores)))
#		
#	return finalScoresDict

def getFeatures(dids, bm25Scores, clfScores):
	bm25s = [bm25Scores[did] for did in dids]
	clfs = [clfScores[did] for did in dids]
	return zip(dids, zip(bm25s, clfs))
	
def writeFeatures(qid, relevance, features, out):
	for did, scores in features:
		out.write("%d qid:%d\t\t" % (relevance, qid))
		for fnum, fval in enumerate(scores, 1):
			out.write("%d:%f\t\t" % (fnum, fval))
		out.write("# %d" % did)
		out.write("\n")
		
def writeDocIds(dids, out):
	for did in dids:
		out.write("%d\n" % did)

def writeTrainingFeatures(bm25Scores, clfScores, outFile):
	print "Writing train features"
	out = open(outFile, "w")
	didsOut = open(outFile + ".doc-ids.txt", "w")
	
	for qid in QUERY_RANGE:
		if qid in BAD_TRAINING_QUERIES[TARGET]:
			print "Query %d bad, ignoring" % qid
			continue
		queryQrels = QRELS[qid]
		queryScores = bm25Scores[qid]
		availDocs = set(clfScores.keys()) & set(queryScores.keys())

		positiveDocs = list(set([did for (did, rel) in queryQrels if rel > 0]) & availDocs)
		negativeDocs = list(set([did for (did, rel) in queryQrels if rel == 0]) & availDocs)
		negativeDocs = negativeDocs[:len(positiveDocs)]
		
		print "Query %d: %d available docs, %d positive docs, %d negative docs" % (qid, len(availDocs), len(positiveDocs), len(negativeDocs))
		
		writeFeatures(qid, 1, getFeatures(positiveDocs, queryScores, clfScores), out)
		writeFeatures(qid, 0, getFeatures(negativeDocs, queryScores, clfScores), out)
		writeDocIds(positiveDocs + negativeDocs, didsOut)
		
	out.close()
	didsOut.close()
	
def writeTestFeatures(bm25Scores, clfScores, outFile):
	print "Wrinting test features"
	out = open(outFile, "w")
	didsOut = open(outFile + ".doc-ids.txt", "w")
	
	for qid in QUERY_RANGE:
		queryQrels = dict(QRELS[qid])
		for did, bm25 in bm25Scores[qid].items():
			relevance = min(1, queryQrels.get(did, 0))
			out.write("%d qid:%d\t\t1:%f\t\t2:%f\t\t# %d\n" % (relevance, qid, bm25, clfScores[did], did))
			didsOut.write("%d\n" % did)
	
	out.close()
	didsOut.close()
	
def run():
	print "Writing " + sys.argv[3] + " features for " + CLASS_ID + " " + TARGET
	
	print "Reading baselines from", BASELINE_RESULTS_FILE
	bm25Scores = getBaselineScores(BASELINE_RESULTS_FILE)
	
	print "Reading classifier"
	clfScores = getClassifierScores(bm25Scores, MAX_CUTOFF, DIVISION_CUTOFF)
	
	if TRAIN:
		writeTrainingFeatures(bm25Scores, clfScores, FEATURE_FILE)
	else:
		writeTestFeatures(bm25Scores, clfScores, FEATURE_FILE)
	print "Done"
	print "------------------------------"
	
run()

