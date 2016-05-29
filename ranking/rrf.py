#!/bin/python

import os
import sys
import scipy.stats

sys.path.insert(0, "../utils/")
import utils

CLASSIFIER = sys.argv[1]
CLASS_ID = sys.argv[2]

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]

TERRIER_RES_DIR = "../ir-terrier/terrier-core-4.1/var/results/"

MODELS = [\
"BB2",\
"BM25",\
"DFR_BM25",\
"DLH",\
"DLH13",\
"DPH",\
"DFRee",\
"Hiemstra_LM",\
"IFB2",\
"In_expB2",\
"In_expC2",\
"InL2",\
"LemurTF_IDF",\
"LGD",\
"PL2",\
"TF_IDF",\
"BM25_Lucene"\
]

def getRankMap(results):
	docs, ranks, _ = zip(*results)
	return dict(zip(docs, ranks))

def getClassificationRankMap(classificationScores):
	docs, scores = classificationScores.keys(), classificationScores.values()
	ranks = scipy.stats.rankdata(scores, method="min")
	ranks = 1 + max(ranks) - ranks
	return dict(zip(docs, ranks))

def rrf(xs):
	return sum(map(lambda x:1.0/(60+x),xs))

def getTerrierScores(year):
	scores = []
	for model in MODELS:
		scoreFile = os.path.join(TERRIER_RES_DIR, "results-" + str(year) + "-" + model + ".txt")
		scores.append(utils.readResults(scoreFile))
	return scores

def computeRRFScores(year, outputFile):
	terrierScores = getTerrierScores(year)
	classificationRanks = getClassificationRankMap(utils.readClassPredictions(CLASSIFIER, CLASS_ID))
	output = open(outputFile, "w")
	for qid in range(QUERY_OFFSET, QUERY_OFFSET + 10):
		rankMaps = map(lambda scores : getRankMap(scores[qid]), terrierScores)
		docs = set.intersection(*map(lambda rankMap : set(rankMap.keys()), rankMaps)) & set(classificationRanks.keys())

		rrfs = [(doc, rrf([rankMap[doc] for rankMap in rankMaps] \
					+ [classificationRanks[doc]] \
					)) for doc in docs]

		rrfs = sorted(rrfs, key=lambda x:x[1], reverse=True)

		rank = 1
		for doc, score in rrfs:
			output.write("%d Q0 %s %d %f STANDARD\n" % (qid, doc, rank, score))
			rank += 1
	output.close()

computeRRFScores(2014, os.path.join(utils.IR_RESULTS_DIR, "results-2014-" + CLASS_ID + ".txt.reranked.RRF"))
computeRRFScores(2015, os.path.join(utils.IR_RESULTS_DIR, "results-2015-" + CLASS_ID + ".txt.reranked.RRF"))

