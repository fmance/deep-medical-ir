#!/bin/python

import sys
import os
import random
import codecs
import gensim

sys.path.insert(0, "../utils/")
import utils

classifier = sys.argv[1]
CATEGORY = sys.argv[2]

CLASSIFICATION_DATA_DIR = "data/"

qrels2014 = utils.readQrels2014()
qrels2015 = utils.readQrels2015()

def getClassifierScores(classifierExt, category):
	resFile = os.path.join(CLASSIFICATION_DATA_DIR, "res-and-qrels", "results", category, "results.txt." + classifierExt)
	idsFile = os.path.join(CLASSIFICATION_DATA_DIR, "res-and-qrels", "ids.txt")
	scores = scores = map(float, open(resFile).readlines())
	ids = map(int, open(idsFile).readlines())
	return dict(zip(ids, scores))
	
diagClassifier = getClassifierScores(classifier, "diag")	
testClassifier = getClassifierScores(classifier, "test")	
treatClassifier = getClassifierScores(classifier, "treat")
classifiersScoresDict = {"diag":diagClassifier, "test":testClassifier, "treat":treatClassifier}

def precision(qrels):
	good = 0
	total = 0
	good_pos = 0
	total_pos = 0
	for qid, docRels in qrels.items():
		for did, rel in docRels:
			score = -1
			if qid <= 10:
				score = diagClassifier[did]
			elif qid <= 20:
				score = testClassifier[did]
			else:
				score = treatClassifier[did]
			if rel > 0:
				good_pos += int(score > 0)
				total_pos += 1
			predFromRel = int(rel > 0)
			predFromClassifier = int(score > 0)
			good += int(predFromClassifier == predFromRel)
			total += 1
#			rel = int(rel > 0)
#			relevant += int(rel == score)
#			total += 1
	return  good, total, float(good)/total,\
			good_pos, total_pos, float(good_pos)/total_pos
	


def getRelevantQrelDocIds(qrels):
	dids = []
	for qid, docRels in qrels.items():
		for did, rel in docRels:
			if rel > 0:
				if (CATEGORY == "diag" and qid <= 10) or \
				   (CATEGORY == "test" and qid > 10 and qid <= 20) or \
				   (CATEGORY == "treat" and qid > 20):
					dids.append(did)
	return set(dids)

def prec():
	dids = getRelevantQrelDocIds(qrels2014) | getRelevantQrelDocIds(qrels2015)
	good = 0
	classifierScores = classifiersScoresDict[CATEGORY]
	for did in dids:
		if classifierScores[did] > 0:
			good += 1
	return float(good)/len(dids)
			
print precision(qrels2014)
print precision(qrels2015)
print prec()
			
