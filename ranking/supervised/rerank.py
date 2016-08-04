#!/bin/python

from collections import defaultdict
import pprint
import os
import sys

#sys.path.insert(0, "../../utils/")
#import utils

TARGET = sys.argv[1]

IR_RESULTS = "../../ir/results/"
DOC_IDS_FILE = os.path.join(IR_RESULTS, "features-" + TARGET + ".txt.doc-ids.txt")

docIds = map(int, open(DOC_IDS_FILE).read().split())

#BASELINE_SCORES = utils.readResults(os.path.join(IR_RESULTS, "results-" + TARGET[:-5] + ".txt"))

scores = defaultdict(list)
docIdsIndex = 0
for line in open("scores.txt"):
	parts = line.split()
	qid = int(parts[0])
	score = float(parts[2])
	did = docIds[docIdsIndex]
	scores[qid].append((did, score))
	docIdsIndex += 1

rankings = {}
for qid, docScores in scores.items():
	rankings[qid] = sorted(docScores, reverse=True, key=lambda kv:kv[1])

out = open("results-reranked.txt", "w")
for qid, docScores in rankings.items():
#	if qid >= 10 and qid <= 20: # !!! don't rerank test queries
#		for did, rank, score in BASELINE_SCORES[qid]:
#		    out.write("%d Q0 %d %d %f STANDARD\n" % (qid, did, rank, score))
#	else:
		rank = 1
		for did, score in docScores:
		    out.write("%d Q0 %d %d %f STANDARD\n" % (qid, did, rank, score))
		    rank += 1
		    score -= 1
        
out.close()
