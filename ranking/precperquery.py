#!/bin/python

import os
import sys
import subprocess


trecEval = "../eval/trec_eval.9.0/trec_eval"
QRELS = sys.argv[1]
RESULTS = sys.argv[2]

def getPrecsPerQuery(precNum):
	output = subprocess.Popen([trecEval, "-q", QRELS, RESULTS], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	
	precMap = {}
	for i in range(0, len(output)):
		if output[i] == precNum and output[i+1] != "all":
			qid = int(output[i+1])
			prec = float(output[i+2])
			precMap[qid] = prec
	
	return precMap
	
precs = getPrecsPerQuery("P_10")
for qid, prec in precs.items():
	#if qid <= 10 or qid > 20:
		print "%.2f" % (prec)
