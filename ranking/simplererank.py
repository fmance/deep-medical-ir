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
import rankutils
import weights

CLASS_ID = sys.argv[1]
TARGET = sys.argv[2]
YEAR = TARGET[:4]

op = OptionParser()
op.add_option("--sgd_weight",
			  action="store", type=float, default=0.5,
			  help="weight of sgd vs sgd+basic.")
op.add_option("--classifier",
			  action="store", default="SGDClassifier.squared_loss.l2",
			  help="classifier.")

(opts, args) = op.parse_args()


USE_HEDGES = False

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]
QUERY_RANGE = range(QUERY_OFFSET, QUERY_OFFSET + 10)

QRELS_FILE = "../data/qrels/qrels-treceval-" + YEAR + ".txt"
BASELINE_RESULTS_FILE = "../ir/results/results-" + TARGET.replace("-unexpanded", "") + ".txt"
EVAL_PROGNAME = "../eval/trec_eval.9.0/trec_eval"

QRELS = utils.readQrels(QRELS_FILE)

if opts.classifier == "all":
	CLASSIFIERS = [
		"Basic",
		"LinearSVC.squared_hinge.l2", 
		"SGDClassifier.hinge.l2",
		"SGDClassifier.hinge.elasticnet",
		"SGDClassifier.squared_loss.l2",
		"SGDClassifier.squared_loss.elasticnet",
		"SGDClassifier.epsilon_insensitive.l2",
		"SGDClassifier.epsilon_insensitive.elasticnet",
		"Pipeline.epsilon_insensitive.l2"
	]
else:
	CLASSIFIERS = [opts.classifier]
	
def interpolate(bm25, classifierScore, topicModelScore, doc2vecScore, w, cw, tw):
	if classifierScore == None:
		return bm25 * w
	if classifierScore < -10:
		return bm25 * w
	else:
		clsW = (1-w)*(math.pow(bm25, 0.5))
		if topicModelScore == None:
			return w * bm25 + clsW * classifierScore
		else:
			return w * bm25 + clsW * (cw*classifierScore + (1-cw)*(tw * topicModelScore + (1-tw) * doc2vecScore))

TOPIC_MODEL_SCORES = utils.readTopicModels(TARGET.replace("-exp", ""))
DOC2VEC_SCORES = utils.readDoc2VecScores(TARGET.replace("-exp", "").replace("-unexpanded", ""))

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
	w = opts.sgd_weight
	if CLASS_ID == "test":
		w *= 0.5
	return w * sgd + (1-w) * basic

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
	
#	mean = np.mean([final for (final, _, _) in finalScores.values()])
#	stdev = np.std([final for (final, _, _) in finalScores.values()])
#	finalScores = {did: ((final-mean)/stdev, sgd, basic) for (did, (final, sgd, basic)) in finalScores.items()}
	
#	writeCombinedScores(finalScores)
	
	return defaultdict(lambda: (0,-10000,-10000), finalScores)

def getP10(qrelsFile, resultsFile):
	output = subprocess.Popen([EVAL_PROGNAME, qrelsFile, resultsFile], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	index = output.index("P_10")
	return float(output[index + 2])

def getP10fromScores(rerankedScores):
	allP10s = []
	for qid, docScores in rerankedScores.items():
		top10Docs = set([doc for (doc, _) in docScores[:10]])
		relDocs = set([did for (did, rel) in QRELS[qid] if rel > 0])
		p10 = float(len(top10Docs & relDocs)) / 10.0
		allP10s.append(p10)
	return np.mean(allP10s), allP10s

def qrelStr(rel):
	return str(rel) if rel != 0 else ""
def classifierStr(scores):
	return "%+.2f\t%+.2f\t%+.2f" % scores
	
def rerankScores(bm25Weight, classifierWeight, topicModelWeight, baselineScores, classifierScores, rerankedFile):
#	out = open(rerankedFile, "w")
	allP10s = []
	for qid in QUERY_RANGE:
		queryQrels = dict(QRELS[qid])
		queryScores = baselineScores[qid]
		queryTopicModel = TOPIC_MODEL_SCORES[qid]
		queryDoc2Vec = DOC2VEC_SCORES[qid]
		
#		if weight == 0.2:
#			bm25Docs = set(queryScores.keys())
#			topicDocs = set(TOPIC_MODEL_SCORES[qid].keys())
#			print "qid %d,  intersection %d, missing %d" % (qid, len(bm25Docs & topicDocs), len(bm25Docs - topicDocs))
#			relBm25Docs = [did for did in bm25Docs if queryQrels.get(did) > 0]
#			relTopicDocs = [did for did in topicDocs if queryQrels.get(did) > 0]
#			print len(relBm25Docs), len(relTopicDocs)
#			
#			print "missing and relevant: ",
#			print [did for did in bm25Docs - topicDocs if queryQrels.get(did) > 0],
#			print " out of: ",
#			print [did for did in bm25Docs if queryQrels.get(did) > 0]
#			print "---------------------------------------"
		
		rerankedScores = [(did, interpolate(queryScores[did][1],
											classifierScores[did][0],
											queryTopicModel[did],
											queryDoc2Vec[did],
											bm25Weight,
											classifierWeight,
											topicModelWeight))
						   for did in queryScores.keys()]
		rerankedScores.sort(key = lambda docScore : docScore[1], reverse = True)
		
		top10Docs = set([doc for (doc, _) in rerankedScores[:10]])
		relDocs = set([did for (did, rel) in queryQrels.items() if rel > 0])
		p10 = float(len(top10Docs & relDocs)) / 10.0
		allP10s.append(p10)
		
#		rank = 1
#		for did, score in rerankedScores:
#			out.write("%d Q0 %s %d %f STANDARD\t#\t%f\t%d\t%f\t%s\t%f\t\t%s\n" %
#							(qid, did, rank, score,
#							bm25Weight, queryScores[did][0], queryScores[did][1], classifierStr(classifierScores[did]),
#							queryTopicModel[did], qrelStr(queryQrels.get(did))))
#			rank += 1
#	out.close()
	return np.mean(allP10s), allP10s

def printAllp10sToFile(allP10s):
	out = open(CLASS_ID + "-" + TARGET + ".txt", "w")
	for w, cw, tw, p10, p10List in allP10s:
		out.write("%f %f %f %s\n" % (w, cw, p10, " ".join(map(str, p10List))))
	out.close()

def lambdaRerank(qrelsFile, baselineScores, classifierScores, rerankedFile):
	allP10 = []
	maxP10 = 0.0
	topicModelWeight = weights.getTopicModelWeight(CLASS_ID, TARGET) 
	
	for bm25Weight in np.linspace(0.0, 1.0, 101):
		print bm25Weight
		for classifierWeight in np.linspace(0.0, 1.0, 101): # [1]:
			
			p10Avg, p10List = rerankScores(bm25Weight, classifierWeight, topicModelWeight, baselineScores, classifierScores, rerankedFile)
			maxP10 = max(p10Avg, maxP10)
			allP10.append((bm25Weight, classifierWeight, topicModelWeight, p10Avg, p10List))
#			print "%f," % p10,
	
	printAllp10sToFile(allP10)

	bestWeights = [(bm25Weight, classifierWeight) for (bm25Weight, classifierWeight, topicModelWeight, p10, p10List) in allP10 if p10 == maxP10]
	baselineP10 = allP10[-1][3]
	
	print "Baseline=%f -> MaxP10=%f lambda=%f/%f" % (baselineP10, maxP10, bestWeights[0][0], bestWeights[0][1])

#	rerankScores(bestWeights[0][0], bestWeights[0][1], baselineScores, classifierScores, rerankedFile)
	return maxP10, allP10

def run():
	baselineScores = getBaselineScores(BASELINE_RESULTS_FILE)
	classifierScores = getClassifierScores()
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID
 	lambdaRerank(QRELS_FILE, baselineScores, classifierScores, rerankedFile)

run()

def rerankKnownWeights():
	baselineScores = getBaselineScores(BASELINE_RESULTS_FILE)
	classifierScores = getClassifierScores()
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID
	
	bm25Weight = weights.getBm25Weight(CLASS_ID, TARGET)
	classifierWeight = weights.getClassifierWeight(CLASS_ID, TARGET)
	topicModelWeight = 1.0 # weights.getTopicModelWeight(CLASS_ID, TARGET)
	
	rerankScores(bm25Weight, classifierWeight, topicModelWeight, baselineScores, classifierScores, rerankedFile)

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



