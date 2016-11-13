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
import weights

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
			  action="store", default="SVMPerf.04.0.001.hedges",
			  help="classifier.")
			  
(opts, args) = op.parse_args()

print "Using classifier", opts.classifier

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]
QUERY_RANGE = range(QUERY_OFFSET, QUERY_OFFSET + 10)

QRELS_FILE = "../data/qrels/qrels-treceval-" + YEAR + ".txt"

if TRAIN:
	BASELINE_RESULTS_FILE = "../ir/results/bm25-" + TARGET.replace("-unexpanded", "") + ".txt"
	FEATURE_FILE = "../ir/results/features-" + CLASS_ID + "-" + TARGET + "-" + opts.classifier + "-train.txt"
else:
	BASELINE_RESULTS_FILE = "../ir/results/results-" + TARGET.replace("-unexpanded", "") + ".txt"
	FEATURE_FILE = "../ir/results/features-" + CLASS_ID + "-" + TARGET + "-" + opts.classifier + "-test.txt"
	
BM25_WEIGHT = 0.64	

QRELS = utils.readQrels(QRELS_FILE)

if "." in opts.classifier:
	CLASSIFFIER_ROOT = opts.classifier[:opts.classifier.index(".")]
else:
	CLASSIFFIER_ROOT = opts.classifier

DIVISION_CUTOFF = weights.DIVISION_CUTOFFS[CLASSIFFIER_ROOT]
MAX_CUTOFF = weights.MAX_CUTOFFS[CLASSIFFIER_ROOT]
BASIC_WEIGHT = weights.BASIC_WEIGHTS[CLASSIFFIER_ROOT]

BAD_TRAINING_QUERIES = {"2014-sum": {17, 25}, # 0% prec: 17, 25; 10%: 3, 6, 10, 11, 13, 18, 19, 23, 29
						"2014-desc": {3, 5, 12, 13, 18, 23, 29}, # 0% prec: 3, 5, 12, 13, 18, 23, 29;  10%: 1, 6, 17, 19, 25
						"2015-sum": {5, 18, 20, 24, 25, 27}, # 0% prec: 5, 18, 20, 24, 25, 27; 10%: 2, 12, 28
						"2015-desc" : {5, 18, 20, 24, 25, 27}, # 0% prec: 5, 18, 20, 24, 25, 27; 10%: 7, 9, 10, 12
						"2016-sum": {4, 10, 19, 21, 22, 23, 25, 27},
						"2016-desc": {2, 3, 5, 10, 13, 19, 22, 23},
						"2016-note": {2, 3, 5, 7, 12, 13, 14, 22, 28},
					}

def getFeatures(dids, bm25Scores, clfScores):
	bm25s = [bm25Scores[did] for did in dids]
	clfs = [clfScores[did][0] for did in dids]
	fused = map(utils.interpolate, bm25s, clfs, [BM25_WEIGHT] * len(bm25s))
	return zip(dids, zip(bm25s, clfs, fused))
	
def writeFeatures(qid, relevances, features, out):
	amendedQid = qid
	if YEAR == "2015":
		amendedQid = qid + 30
	if YEAR == "2016":
		amendedQid = qid + 60
	for relevance, (did, scores) in zip(relevances, features):
		out.write("%d qid:%d\t\t" % (relevance, amendedQid))
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
		queryQrelsDict = dict(queryQrels)
		
		queryScores = bm25Scores[qid]
		availDocs = set(clfScores[qid].keys()) & set(queryScores.keys())

		positiveDocs = list(set([did for (did, rel) in queryQrels if rel > 0]) & availDocs)
		negativeDocs = list(set([did for (did, rel) in queryQrels if rel == 0]) & availDocs)
#		negativeDocs = negativeDocs[:len(positiveDocs)]
		docFilter = set(positiveDocs)|set(negativeDocs)
		
		print "ClfScoresFilter"
		clfScoresFiltered = utils.getClassifierScores(CLASS_ID, opts.classifier, bm25Scores, BASIC_WEIGHT, MAX_CUTOFF, DIVISION_CUTOFF,
														normalize=False, docFilter=docFilter)
	
		positiveRels = [queryQrelsDict[did] for did in positiveDocs]
	
		print "Query %d: %d available docs, %d positive docs, %d negative docs" % (qid, len(availDocs), len(positiveDocs), len(negativeDocs))
		
		writeFeatures(qid, positiveRels, getFeatures(positiveDocs, queryScores, clfScoresFiltered[qid]), out)
		writeFeatures(qid, [0] * len(negativeDocs), getFeatures(negativeDocs, queryScores, clfScoresFiltered[qid]), out)
		writeDocIds(positiveDocs + negativeDocs, didsOut)
		
	out.close()
	didsOut.close()
	
def writeTestFeatures(bm25Scores, clfScores, outFile):
	print "Wrinting test features"
	out = open(outFile, "w")
	didsOut = open(outFile + ".doc-ids.txt", "w")
	
	for qid in QUERY_RANGE:
		queryQrels = dict(QRELS[qid])
		for did, bm25Score in bm25Scores[qid].items():
			relevance = queryQrels.get(did, 0)
#			relevance = min(1, relevance)
			clfScore = clfScores[qid][did][0]
			fused = utils.interpolate(bm25Score, clfScore, BM25_WEIGHT)
			out.write("%d qid:%d\t\t1:%f\t\t2:%f\t\t3:%f\t\t# %d\n" % (relevance, qid, bm25Score, clfScore, fused, did))
			didsOut.write("%d\n" % did)
	
	out.close()
	didsOut.close()
	
def run():
	print "Writing " + sys.argv[3] + " features for " + CLASS_ID + " " + TARGET
	
	print "Reading baselines from", BASELINE_RESULTS_FILE
	bm25Scores = utils.getBaselineScores(BASELINE_RESULTS_FILE, QUERY_RANGE)
	for qid, docRanksScores in bm25Scores.items():
		docs = docRanksScores.keys()
		ranks, scores = zip(*(docRanksScores.values()))
		bm25Scores[qid] = dict(zip(docs, utils.minMaxNormalizeList(scores)))
	
	print "Reading classifier"
	clfScores = utils.getClassifierScores(CLASS_ID, opts.classifier, bm25Scores, BASIC_WEIGHT, MAX_CUTOFF, DIVISION_CUTOFF, normalize=False)
	
	if TRAIN:
		writeTrainingFeatures(bm25Scores, clfScores, FEATURE_FILE)
	else:
		writeTestFeatures(bm25Scores, clfScores, FEATURE_FILE)
	print "Done"
	print "------------------------------"
	
run()

