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
op.add_option("--fusion",
			  action="store", default="interpolation",
			  help="fusion method.")
op.add_option("--max_cutoff",
			  action="store", type=float, default=2.0,
			  help="max cutoff.")
op.add_option("--division_cutoff",
			  action="store", type=float, default=4.0,
			  help="division cutoff.")

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
		"BernoulliNB",
		"MultinomialNB",
		"NearestCentroid",
		"PassiveAggressiveClassifier.hinge",
		"Perceptron",
		"RidgeClassifier",
		"RandomForestClassifier",
		"LinearSVC.squared_hinge.l2",
		"SGDClassifier.log.l2",
		"SGDClassifier.log.elasticnet",
		"SGDClassifier.hinge.l2",
		"SGDClassifier.hinge.elasticnet",
		"SGDClassifier.squared_hinge.l2",
		"SGDClassifier.squared_hinge.elasticnet",
		"SGDClassifier.squared_loss.l2",
		"SGDClassifier.squared_loss.elasticnet",
		"SGDClassifier.epsilon_insensitive.l2",
		"SGDClassifier.epsilon_insensitive.elasticnet",
		"Pipeline.epsilon_insensitive.l2",
		"NN"
	]
else:
	CLASSIFIERS = [opts.classifier]
	
if "." in opts.classifier:
	CLASSIFFIER_ROOT = opts.classifier[:opts.classifier.index(".")]
else:
	CLASSIFFIER_ROOT = opts.classifier

DIVISION_CUTOFF = opts.division_cutoff
MAX_CUTOFF = opts.max_cutoff

DIVISION_CUTOFFS = {"SVMPerf" : 4.0,
					"SGDClassifier": 6.0,
					"LinearSVC" : 3.5}
DIVISION_CUTOFF = DIVISION_CUTOFFS.get(CLASSIFFIER_ROOT, opts.division_cutoff)

MAX_CUTOFFS = {"SVMPerf" : 1.0,
			   "SGDClassifier":1.0,
			   "LinearSVC" : 1.0}
MAX_CUTOFF = MAX_CUTOFFS.get(CLASSIFFIER_ROOT, opts.max_cutoff)

BASIC_WEIGHTS = {"SVMPerf": 0.1,
				 "SGDClassifier": 0.5,
				 "LinearSVC" : 0.0}
BASIC_WEIGHT = BASIC_WEIGHTS.get(CLASSIFFIER_ROOT, 0.0)

if "SGDClassifier" in opts.classifier:
	if CLASS_ID == "diag":
		DIVISION_CUTOFF = 12.0
	elif CLASS_ID == "test":
		DIVISION_CUTOFF = 11.0
	elif CLASS_ID == "treat":
		DIVISION_CUTOFF = 4.0

def rrf(rank1, rank2, weight):
#	if CLASS_ID == "diag":
#		return 1.0 / (60+rank1)
	return 1.0/(60 + rank1) * weight + 1.0/(60 + rank2) * (1-weight)
	
def borda(rank1, rank2, weight):
#	if CLASS_ID == "diag":
#		return 1.0/rank1
	return 1.0 / (weight * rank1 + (1-weight) * rank2)

def interpolate(bm25, classifierScore, w):
#	if CLASS_ID == "test" and YEAR == "2015":
#		return bm25
	
	if classifierScore == None:
		print "ERROR X"
		return bm25 * w
	if classifierScore < -10:
		print "ERROR Y: ", classifierScore
		return bm25 * w
	else:
		clsW = (1-w) #### *(math.pow(bm25, 0.5)) TODO should we use this ???
		return w * bm25 + clsW * classifierScore #(cw*classifierScore + (1-cw)*(tw * topicModelScore + (1-tw) * doc2vecScore))

#TOPIC_MODEL_SCORES = utils.readTopicModels(TARGET.replace("-exp", ""))
#DOC2VEC_SCORES = utils.readDoc2VecScores(TARGET.replace("-exp", "").replace("-unexpanded", ""))

def zscoreDictValues(d):
	return dict(zip(d.keys(), stats.zscore(d.values())))

def minMaxNormalizeList(ls):
	minLs = min(ls)
	maxLs = max(ls)
	if minLs == maxLs:
		return [0] * len(ls)
	else:
		return [(x-minLs)/(maxLs-minLs) for x in ls]

def getBaselineScores(baselineResultsFile):
	baselineResults = utils.readResults(baselineResultsFile)
	normScores = {}
	for qid in QUERY_RANGE:
		docs, ranks, scores = zip(*(baselineResults[qid]))
		### TODO TODO Maybe use log bm25
		normScores[qid] = dict(zip(docs, zip(ranks, [bm25 for bm25 in minMaxNormalizeList(scores)])))
	return normScores

def writeCombinedScores(finalScores):
	if CLASS_ID != "test":
		docIds = utils.readInts(os.path.join(utils.RES_AND_QRELS_DIR, "ids.txt"))
		out = open(os.path.join(utils.RES_AND_QRELS_DIR, "results", CLASS_ID, "results.txt.Combined"), "w")
		for did in docIds:
			out.write("%f\n" % (finalScores[did][0]))
		out.close()

def combineScores(basic, sgd):
	w = BASIC_WEIGHT #opts.sgd_weight
#	if CLASS_ID == "test":
#		sgd /= 2.0
	return (1-w) * sgd + w * basic

def getClassifierScores(baselineScores, maxCutoff, divisionCutoff):
	clfScores = defaultdict(float)
	for classifier in CLASSIFIERS:
		for did, score in utils.readClassPredictions(classifier, CLASS_ID, True, USE_HEDGES).items():
			clfScores[did] += score #(1.0 if score > 0 else 0.0)
	clfScores = {did: score/len(CLASSIFIERS) for did, score in clfScores.items()}

	basicScores = utils.readClassPredictions("Basic", CLASS_ID, False, False)
	basicScores = {did: min(maxCutoff, float(score)/divisionCutoff) for did, score in basicScores.items()}

	finalScoresDict = {}
	for qid, docScoresDict in baselineScores.items():
		docs = docScoresDict.keys()
		
		queryBasicScores = [basicScores[did] for did in docs]
		queryBasicScores = utils.maxNormalize(queryBasicScores) # TODO ? minmaxnormalize ?
		
		queryClfScores = minMaxNormalizeList([clfScores[did] for did in docs])
		
#		combinedScores = map(lambda (x,y) : BASIC_WEIGHT/(60+x) +  (1-BASIC_WEIGHT)/(60+y),
#									zip(rankList(queryBasicScores), rankList(queryClfScores)))
		combinedScores = map(combineScores, queryBasicScores, queryClfScores)
#		combinedScores = minMaxNormalizeList(combinedScores)
		if CLASS_ID == "test":
			combinedScores = [score/2.0 for score in combinedScores]
		
		finalScoresDict[qid] = dict(zip(docs, zip(combinedScores, queryClfScores, queryBasicScores)))
		
	return finalScoresDict

def rankList(ls):
	inverted = [max(ls)-x for x in ls]
	return stats.rankdata(inverted, method="min")

def computeClassifierRankings(baselineResults, classifierScores):
	if opts.fusion == "interpolation":
		return defaultdict(int)
		
	rankings = {}
	for qid, queryClfScores in classifierScores.items():
		docs = queryClfScores.keys()
		clfScores = [queryClfScores[did][0] for did in docs]
		invertedScores = [max(clfScores)-score for score in clfScores]
		ranks = stats.rankdata(invertedScores, method="min")
		rankings[qid] = dict(zip(docs, ranks))

	return rankings

#def getP10(qrelsFile, resultsFile):
#	output = subprocess.Popen([EVAL_PROGNAME, qrelsFile, resultsFile], stdout=subprocess.PIPE).communicate()[0]
#	output = output.split()
#	index = output.index("P_10")
#	return float(output[index + 2])

#def getP10fromScores(rerankedScores):
#	allP10s = []
#	for qid, docScores in rerankedScores.items():
#		top10Docs = set([doc for (doc, _) in docScores[:10]])
#		relDocs = set([did for (did, rel) in QRELS[qid] if rel > 0])
#		p10 = float(len(top10Docs & relDocs)) / 10.0
#		allP10s.append(p10)
#	return np.mean(allP10s), allP10s

def qrelStr(rel):
	return str(rel) if rel != 0 else ""
def classifierStr(scores):
	return "%+.2f\t%+.2f\t%+.2f" % scores

def rerankScores(bm25Weight, baselineScores, classifierScores, classifierRankings, rerankedFile, writeFile=False):
	if writeFile:
		out = open(rerankedFile, "w")
	allP10s = []
	for qid in QUERY_RANGE:
		queryQrels = dict(QRELS[qid])
		queryScores = baselineScores[qid]
		queryTopicModel = defaultdict(float) # TOPIC_MODEL_SCORES[qid]
		queryDoc2Vec = defaultdict(float) #DOC2VEC_SCORES[qid]
		queryClfRankings = classifierRankings[qid]
		queryClfScores = classifierScores[qid]
		
		if opts.fusion == "interpolation":
			rerankedScores = [(did, interpolate(queryScores[did][1], queryClfScores[did][0], bm25Weight)) for did in queryScores.keys()]
		elif opts.fusion == "rrf":
			rerankedScores = [(did, rrf(queryScores[did][0], queryClfRankings[did], bm25Weight)) for did in queryScores.keys()]
		elif opts.fusion == "borda":
			rerankedScores = [(did, borda(queryScores[did][0], queryClfRankings[did], bm25Weight)) for did in queryScores.keys()]
						   
		rerankedScores.sort(key = lambda docScore : docScore[1], reverse = True)
		
		top10Docs = set([doc for (doc, _) in rerankedScores[:10]])
		relDocs = set([did for (did, rel) in queryQrels.items() if rel > 0])
		p10 = float(len(top10Docs & relDocs)) / 10.0
		allP10s.append(p10)
		
		if writeFile:
			rank = 1
			for did, score in rerankedScores:
				out.write("%d Q0 %s %3d %f SUMMARY" % (qid, did, rank, score))
				out.write("\t#\t%f\t%d\t%f\t%s\t%f\t%f\t\t%s\n" %
								(bm25Weight,
								queryScores[did][0],
								queryScores[did][1],
								classifierStr(classifierScores[did]),
								queryTopicModel.get(did, -1),
								queryDoc2Vec.get(did, -1),
								qrelStr(queryQrels.get(did))))
				rank += 1
	
	if writeFile:
		out.close()
	
	return np.mean(allP10s), allP10s

def printAllp10sToFile(allP10s):
	out = open(CLASS_ID + "-" + TARGET + ".txt", "w")
	for w, cw, tw, p10, p10List in allP10s:
		out.write("%f %f %f %s\n" % (w, cw, p10, " ".join(map(str, p10List))))
	out.close()

def lambdaRerank(qrelsFile, baselineScores, classifierScores, classifierRankings, rerankedFile, suppresOutput=False):
	allP10 = []
	maxP10 = 0.0
	classifierWeight = 1.0
	topicModelWeight = 0#weights.getTopicModelWeight(CLASS_ID, TARGET) 
	
	for bm25Weight in np.linspace(0.0, 1.0, 51):
#		print bm25Weight
#		for classifierWeight in [1]: #np.linspace(0.0, 1.0, 101): # [1]:
		p10Avg, p10List = rerankScores(bm25Weight, baselineScores, classifierScores, classifierRankings, rerankedFile)
		maxP10 = max(p10Avg, maxP10)
		allP10.append((bm25Weight, classifierWeight, topicModelWeight, p10Avg, p10List))
		if not suppresOutput:
			print "%f" % p10Avg
	
#	printAllp10sToFile(allP10)

	bestWeights = [(bm25Weight, classifierWeight) for (bm25Weight, classifierWeight, topicModelWeight, p10, p10List) in allP10 if p10 == maxP10]
	baselineP10 = allP10[-1][3]
	
	if not suppresOutput:
		print "Baseline=%f -> MaxP10=%f lambda=%f" % (baselineP10, maxP10, bestWeights[0][0]) #, bestWeights[0][1])

#	rerankScores(bestWeights[0][0], baselineScores, classifierScores, classifierRankings, rerankedFile, writeFile=True)
	return maxP10, allP10

def run():
	baselineScores = getBaselineScores(BASELINE_RESULTS_FILE)
	classifierScores = getClassifierScores(baselineScores, MAX_CUTOFF, DIVISION_CUTOFF)
	classifierRankings = computeClassifierRankings(baselineScores, classifierScores)
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID + "." + opts.classifier + "." + opts.fusion
 	lambdaRerank(QRELS_FILE, baselineScores, classifierScores, classifierRankings, rerankedFile)

run()

def varyCutoffs():
	baselineScores = getBaselineScores(BASELINE_RESULTS_FILE)
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID + "." + opts.classifier + "." + opts.fusion
	
	allP10Dict = defaultdict(float)
	for maxCutoff in np.linspace(1,3,9):
		for divisionCutoff in np.linspace(1,6,21):
			classifierScores = getClassifierScores(maxCutoff, divisionCutoff)
			classifierRankings = computeClassifierRankings(baselineScores, classifierScores)
		 	maxP10, allP10 = lambdaRerank(QRELS_FILE, baselineScores, classifierScores, classifierRankings, rerankedFile, suppresOutput=True)
		 	
#		 	print "%.2f %.2f %.4f" % (maxCutoff, divisionCutoff, maxP10)
		 	print "%.4f" % maxP10

#varyCutoffs()

def rerankKnownWeights():
	baselineScores = getBaselineScores(BASELINE_RESULTS_FILE)
	classifierScores = getClassifierScores(MAX_CUTOFF, DIVISION_CUTOFF)
	classifierRankings = computeClassifierRankings(baselineScores, classifierScores)
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID + "." + opts.classifier + "." + opts.fusion
	
	bm25Weight = 1.0 #weights.getBm25Weight(CLASS_ID, TARGET)
	
#	print "Weights: %.2f" % (bm25Weight, classifierWeight, topicModelWeight)
	
	p10Avg, p10List = rerankScores(bm25Weight, baselineScores, classifierScores, classifierRankings, rerankedFile, writeFile=True)
	print "%.2f" % p10Avg
#	print p10List

#rerankKnownWeights()

def getRandomClassifiers(dids, num):
	classifiers = []
	for _ in range(0, num):
#		classifiers.append(dict(zip(dids, np.random.choice([0, 1], size=len(dids)))))
		randomNums = np.random.uniform(0, 1, size=len(dids))
		classifiers.append(dict(zip(dids, zip(randomNums, randomNums, randomNums))))
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
			p10, _ = rerankScores(weight, baselineScores, randomClassifiers[i], rerankedFile)
			sumP10 += p10
		avgP10 = sumP10/numIter
		maxP10 = max(avgP10, maxP10)
		print round(avgP10, 3)
	print "MaxP10=%f" % maxP10
	
#random(50)



