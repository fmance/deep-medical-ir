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
from optparse import OptionParser

sys.path.insert(0, "../utils/")
import utils
import rankutils


CLASS_ID = sys.argv[1]
TARGET = sys.argv[2]
YEAR = TARGET[:4]

# parse commandline arguments
#op = OptionParser()
#op.add_option("--classifier_weight",
#			  action="store", type=float, default=1.0,
#			  help="weight of classifier w.r.t classifier+topicModel.")

#(opts, args) = op.parse_args()

USE_HEDGES = False

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]
QUERY_RANGE = range(QUERY_OFFSET, QUERY_OFFSET + 10)

QRELS_FILE = "../data/qrels/qrels-treceval-" + YEAR + ".txt"
BASELINE_RESULTS_FILE = "../ir/results/results-" + TARGET + ".txt"
EVAL_PROGNAME = "../eval/trec_eval.9.0/trec_eval"

QRELS = utils.readQrels(QRELS_FILE)

CLASSIFIERS = [
#	"Basic",
#	"LinearSVC.squared_hinge.l2", 
#	"SGDClassifier.hinge.l2",
#	"SGDClassifier.hinge.elasticnet",
	"SGDClassifier.squared_loss.l2",
#	"SGDClassifier.squared_loss.elasticnet",
#	"SGDClassifier.epsilon_insensitive.l2",
#	"SGDClassifier.epsilon_insensitive.elasticnet",
#	"Pipeline.epsilon_insensitive.l2"
]

#if len(sys.argv) > 3 and sys.argv[3] != "all":
#	CLASSIFIERS = [sys.argv[3]]

def interpolate(bm25, classifierScore, topicModelScore, w, cw):
	if classifierScore == None:
		return bm25 * w
	if classifierScore < -10:
		return bm25 * w
	else:
		if topicModelScore == None:
			return w * bm25 + (1-w) * classifierScore
		else:
#			cw = opts.classifier_weight
			return w * bm25 + (1-w) * (cw*classifierScore + (1-cw)*topicModelScore)

TOPIC_MODEL_SCORES = utils.readTopicModels(YEAR)

def zscoreDictValues(d):
	return dict(zip(d.keys(), stats.zscore(d.values())))

def getBaselineScores(baselineResultsFile):
	baselineResults = utils.readResults(baselineResultsFile)
	normScores = {}
	for qid in QUERY_RANGE:
		doc, ranks, scores = zip(*(baselineResults[qid]))
		normScores[qid] = dict(zip(doc, zip(ranks, [bm25 for bm25 in utils.maxNormalize(scores)])))
	return normScores

def writeCombinedScores(finalScores):
	if CLASS_ID != "test":
		docIds = utils.readInts(os.path.join(utils.RES_AND_QRELS_DIR, "ids.txt"))
		out = open(os.path.join(utils.RES_AND_QRELS_DIR, "results", CLASS_ID, "results.txt.Combined"), "w")
		for did in docIds:
			out.write("%f\n" % (finalScores[did][0]))
		out.close()

def combineScores(basic, sgd):
	if sgd == 0 and basic == 0:
		final = -1
	else:
#		if len(sys.argv) == 4:
#			w = float(sys.argv[3])
#		else:
#			w = 0.5
		w = 0.5
		
		if CLASS_ID == "test":
			w *= 0.5

		final = w * sgd + (1-w) * basic
	return final

def getClassifierScores():
	scores = defaultdict(float)
	for classifier in CLASSIFIERS:
		for did, score in utils.readClassPredictions(classifier, CLASS_ID, True, USE_HEDGES).items():
			scores[did] += score
	scores = {did: score/len(CLASSIFIERS) for did, score in scores.items()}
	basicScores = utils.readClassPredictions("Basic", CLASS_ID, False, False)
	finalScores = {}
	for did in scores.keys():
		sgd = scores[did]
		basic = basicScores[did]
		final = combineScores(basic, sgd)
		finalScores[did] = (final, sgd, basic)
		
	maxScore = max([final for (final, _, _) in finalScores.values()])
	finalScores = {did: (final/maxScore, sgd, basic) for (did, (final, sgd, basic)) in finalScores.items()}
	
	writeCombinedScores(finalScores)
	
	return defaultdict(lambda: (0,-10000,-10000), finalScores)

def getP10(qrelsFile, resultsFile):
	output = subprocess.Popen([EVAL_PROGNAME, qrelsFile, resultsFile], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	index = output.index("P_10")
	return float(output[index + 2])

def getP10fromScores(rerankedScores):
	p10 = 0.0
	for qid, docScores in rerankedScores.items():
		top10Docs = set([doc for (doc, _) in docScores[:10]])
		relDocs = set([did for (did, rel) in QRELS[qid] if rel > 0])
		p10 += float(len(top10Docs & relDocs))/10
	return p10/len(QUERY_RANGE)

def qrelStr(rel):
	return str(rel) if rel != 0 else ""
def classifierStr(scores):
	return "%+.2f\t%+.2f\t%+.2f" % scores
	
def rerankScores(weight, classifierWeight, baselineScores, classifierScores, rerankedFile):
	out = open(rerankedFile, "w")
	rerankedScoresDict = {}
	for qid in QUERY_RANGE:
		queryQrels = dict(QRELS[qid])
		queryScores = baselineScores[qid]
		queryTopicModel = TOPIC_MODEL_SCORES[qid]
		
#		if weight == 0.2:
#			bm25Docs = set(queryScores.keys())
#			topicDocs = set(TOPIC_MODEL_SCORES[qid].keys())
#			print "qid %d,  intersection %d, missing %d" % (qid, len(bm25Docs & topicDocs), len(bm25Docs - topicDocs))
#			relBm25Docs = [did for did in bm25Docs if queryQrels.get(did) > 0]
#			relTopicDocs = [did for did in topicDocs if queryQrels.get(did) > 0]
##			print len(relBm25Docs), len(relTopicDocs)
#			
#			print "missing and relevant: ",
#			print [did for did in bm25Docs - topicDocs if queryQrels.get(did) > 0],
#			print " out of: ",
#			print [did for did in bm25Docs if queryQrels.get(did) > 0]
#			print "---------------------------------------"
		
		rerankedScores = [(did, interpolate(queryScores[did][1], classifierScores[did][0], queryTopicModel.get(did), weight, classifierWeight))
						   for did in queryScores.keys()]
		rerankedScores.sort(key = lambda docScore : docScore[1], reverse = True)
		rerankedScoresDict[qid] = rerankedScores
		rank = 1
		for did, score in rerankedScores:
			out.write("%d Q0 %s %d %f STANDARD\t#\t%f\t%d\t%f\t%s\t\t%s\n" %
							(qid, did, rank, score,
							weight, queryScores[did][0], queryScores[did][1], classifierStr(classifierScores[did]), qrelStr(queryQrels.get(did))))
			rank += 1
	out.close()
	return rerankedScoresDict

def printAllp10s(allP10s):
	out = open(CLASS_ID + "-" + YEAR + ".txt", "w")
	for w, cw, p10 in allP10s:
		out.write("%f %f %f\n" % (w, cw, p10))
	out.close()
	
def lambdaRerank(qrelsFile, baselineScores, classifierScores, rerankedFile):
	allP10 = []
	maxP10 = 0.0
	for weight in np.linspace(0.2,1,81):
		for classifierWeight in np.linspace(0.0, 1.0, 101): # [1]:
			rerankedScores = rerankScores(weight, classifierWeight, baselineScores, classifierScores, rerankedFile)
	#		p10 = getP10(qrelsFile, rerankedFile)
			p10 = getP10fromScores(rerankedScores)
			maxP10 = max(p10, maxP10)
			allP10.append((weight, classifierWeight, p10))
			print "%f %f %f," % (weight, classifierWeight, p10),
#			print "%f," % p10,
		print

	bestWeights = [(weight, classifierWeight) for (weight, classifierWeight, p10) in allP10 if p10 == maxP10]
	baselineP10 = allP10[-1][2]
	
	print "\nBaseline=%f -> MaxP10=%f lambda=%f/%f" % (baselineP10, maxP10, bestWeights[0][0], bestWeights[0][1])

#	printAllp10s(allP10)
	rankutils.printBestWeights(bestWeights)	
#	rankutils.plotAllp10s(allP10)

#	rerankScores(0.62, 0.99, baselineScores, classifierScores, rerankedFile)
	rerankScores(bestWeights[0][0], bestWeights[0][1], baselineScores, classifierScores, rerankedFile)
	return maxP10, allP10

def run():
	baselineScores = getBaselineScores(BASELINE_RESULTS_FILE)
	classifierScores = getClassifierScores()
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID
 	lambdaRerank(QRELS_FILE, baselineScores, classifierScores, rerankedFile)

#run()

def rerankKnownWeights():
	baselineScores = getBaselineScores(BASELINE_RESULTS_FILE)
	classifierScores = getClassifierScores()
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID
	rerankScores(0.39, 0.15, baselineScores, classifierScores, rerankedFile)

#rerankKnownWeights()

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



