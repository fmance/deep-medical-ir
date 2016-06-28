#!/bin/python

import os
import sys
import subprocess

trecEval = "../eval/trec_eval.9.0/trec_eval"

CLASS_ID = sys.argv[1]
YEAR = sys.argv[2]

QRELS = "../data/qrels/qrels-treceval-" + YEAR + ".txt"
RESULTS = "../ir/results/results-" + YEAR + ".txt"

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]
QUERY_RANGE = range(QUERY_OFFSET, QUERY_OFFSET + 10)

def getPrecsPerQuery(precNum, results):
	output = subprocess.Popen([trecEval, "-q", QRELS, results], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	
	precMap = {}
	for i in range(0, len(output)):
		if output[i] == precNum and output[i+1] != "all":
			qid = int(output[i+1])
			prec = float(output[i+2])
			precMap[qid] = prec
	
	return precMap
	
precs = getPrecsPerQuery("P_10", RESULTS)
precsReranked = getPrecsPerQuery("P_10", RESULTS + ".reranked." + CLASS_ID)
sumPrec = 0.0
sumPrecReranked = 0.0
for qid, prec in precs.items():
	if qid in QUERY_RANGE:
		print "%d\t%.2f\t%.2f\t" % (qid, prec, precsReranked[qid]),
		if precsReranked[qid] != prec:
			print "%+.2f" % (precsReranked[qid] - prec)
		else:
			print
		sumPrec += prec
		sumPrecReranked += precsReranked[qid]
		
print "-" * 40
print "avg\t%.2f\t%.2f\t%+.2f" % (sumPrec/len(QUERY_RANGE), sumPrecReranked/len(QUERY_RANGE), (sumPrecReranked-sumPrec)/len(QUERY_RANGE))
