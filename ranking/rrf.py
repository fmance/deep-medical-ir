#!/bin/python

import os
import sys
import scipy.stats

sys.path.insert(0, "../utils/")
import utils

CLASSIFIER = sys.argv[1]
MODEL=sys.argv[2]
CLASS_ID = sys.argv[3]

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]

def getRankMap(results):
	docs, ranks, _ = zip(*results)
	return dict(zip(docs, ranks))
	
#	rankMax=max(ranks)
#	return dict(zip(docs, [rankMax-r for r in ranks]))

def getClassificationRankMap(classificationScores):
	docs, scores = classificationScores.keys(), classificationScores.values()
	ranks = scipy.stats.rankdata(scores, method="min")
	ranks = 1 + max(ranks) - ranks
	return dict(zip(docs, ranks))
	
def getClassificationBordaCounts(classificationScores, filterDocs):
	classificationScores = {doc: classificationScores[doc] for doc in filterDocs}
	docs, scores = classificationScores.keys(), classificationScores.values()
	ranks = scipy.stats.rankdata(scores, method="min")
	return dict(zip(docs, ranks))

def rrf(xs):
	return sum(map(lambda x:1.0/(60+x),xs))
	
def getTerrierScoresModel(year):
	scoreFile = os.path.join(utils.IR_RESULTS_DIR, "results-" + str(year) + "-" + MODEL + ".txt")
	return utils.readResults(scoreFile)

CLASSIFICATION_SCORES = utils.readClassPredictions(CLASSIFIER, CLASS_ID)
CLASSIFICATION_RANKS = getClassificationRankMap(CLASSIFICATION_SCORES)

def computeRRFScores(year, outputFile):
	terrierScoresModel = getTerrierScoresModel(year)
	output = open(outputFile, "w")
	for qid in range(QUERY_OFFSET, QUERY_OFFSET + 10):
		rankMap = getRankMap(terrierScoresModel[qid])
		docs = rankMap.keys() #set.intersection(*map(lambda rankMap : set(rankMap.keys()), rankMaps))# & set(classificationRanks.keys())
	
		classificationBordaCounts = getClassificationBordaCounts(CLASSIFICATION_SCORES, docs)
		
		#rrfs = [(doc, rankMap[doc] + classificationBordaCounts[doc]) for doc in docs]
		rrfs = [(doc, rrf([rankMap[doc], CLASSIFICATION_RANKS[doc]])) for doc in docs]

		rrfs = sorted(rrfs, key=lambda x:x[1], reverse=True)
		rank = 1
		for doc, score in rrfs:
			output.write("%d Q0 %s %d %f STANDARD\n" % (qid, doc, rank, score))
			rank += 1
	output.close()

computeRRFScores(2014, os.path.join(utils.IR_RESULTS_DIR, "../results-2014-" + CLASS_ID + ".txt.reranked.RRF"))
computeRRFScores(2015, os.path.join(utils.IR_RESULTS_DIR, "../results-2015-" + CLASS_ID + ".txt.reranked.RRF"))

