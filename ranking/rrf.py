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

def computeRRFScores(bm25ScoresFile, tfidfScoresFile, outputFile):
	bm25Scores = utils.readResults(bm25ScoresFile)
	tfidfScores = utils.readResults(tfidfScoresFile)
	classificationRanks = getClassificationRankMap(utils.readClassPredictions(CLASSIFIER, CLASS_ID))
	output = open(outputFile, "w")
	for qid in range(QUERY_OFFSET, QUERY_OFFSET + 10):
		bm25Ranks = getRankMap(bm25Scores[qid])
		tfidfRanks = getRankMap(tfidfScores[qid])
		docs = set(bm25Ranks.keys()) & set(tfidfRanks.keys())
		rrfs = [(doc, rrf([bm25Ranks[doc], \
						   tfidfRanks[doc], \
						   classificationRanks[doc] \
						   ])) for doc in docs]
		rrfs = sorted(rrfs, key=lambda x:x[1], reverse=True)
		rank = 1
		for doc, score in rrfs:
			output.write("%d Q0 %s %d %f STANDARD\n" % (qid, doc, rank, score))
			rank += 1
	output.close()

computeRRFScores(utils.BM25_SCORES_2014, utils.TFIDF_SCORES_2014, \
				 os.path.join(utils.IR_RESULTS_DIR, "results-2014-" + CLASS_ID + ".txt.reranked.RRF"))
computeRRFScores(utils.BM25_SCORES_2015, utils.TFIDF_SCORES_2015, \
				 os.path.join(utils.IR_RESULTS_DIR, "results-2015-A-" + CLASS_ID + ".txt.reranked.RRF"))	
	
