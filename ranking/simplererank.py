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
			  action="store", default="SVMPerf.04.0.001.hedges",
			  help="classifier.")
op.add_option("--fusion",
			  action="store", default="interpolation",
			  help="fusion method.")
op.add_option("--max_cutoff",
			  action="store", type=float, default=1.0,
			  help="max cutoff.")
op.add_option("--division_cutoff",
			  action="store", type=float, default=4.0,
			  help="division cutoff.")
op.add_option("--no_basic",
			  action="store_true",
			  help="don't use basic classifier.")


(opts, args) = op.parse_args()


USE_HEDGES = False

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21, "all": 1}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]
QUERY_RANGE = range(QUERY_OFFSET, QUERY_OFFSET + 10)
if CLASS_ID == "all":
	QUERY_RANGE = range(1, 31)

QRELS_FILE = "../data/qrels/qrels-treceval-" + YEAR + ".txt"
BASELINE_RESULTS_FILE = "../ir/results/results-" + TARGET.replace("-unexpanded", "") + ".txt"
EVAL_PROGNAME = "../eval/trec_eval.9.0/trec_eval"

QRELS = utils.readQrels(QRELS_FILE)

if "." in opts.classifier:
	CLASSIFFIER_ROOT = opts.classifier[:opts.classifier.index(".")]
else:
	CLASSIFFIER_ROOT = opts.classifier

DIVISION_CUTOFF = weights.DIVISION_CUTOFFS.get(CLASSIFFIER_ROOT, opts.division_cutoff)
MAX_CUTOFF = weights.MAX_CUTOFFS.get(CLASSIFFIER_ROOT, opts.max_cutoff)

BASIC_WEIGHT = weights.BASIC_WEIGHTS.get(CLASSIFFIER_ROOT, 0.0)
if opts.no_basic:
	BASIC_WEIGHT = 0

def rrf(rank1, rank2, weight):
	rrf1 = weight/(60.0 + rank1)
	rrf2 = (1.0-weight)/(60.0 + rank2)
	return rrf1 + rrf2
	
def borda(rank1, rank2, weight):
	return 1.0 / (weight * rank1 + (1-weight) * rank2)

#TOPIC_MODEL_SCORES = utils.readTopicModels(TARGET.replace("-exp", ""))
#DOC2VEC_SCORES = utils.readDoc2VecScores(TARGET.replace("-exp", "").replace("-unexpanded", ""))

def zscoreDictValues(d):
	return dict(zip(d.keys(), stats.zscore(d.values())))

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
		rankings[qid] = dict(zip(docs, map(float, ranks)))

	return rankings

def getP10(qrelsFile, resultsFile):
	output = subprocess.Popen([EVAL_PROGNAME, qrelsFile, resultsFile], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	index = output.index("P_10")
	return float(output[index + 2])

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

def rerankScores(bm25Weight, baselineScores, classifierScores, classifierRankings, rerankedFile, writeFile=False, qrelsDict=QRELS, printUnjudged=False):
	if writeFile:
		out = open(rerankedFile, "w")
	allP10s = []
	unjudged = 0.0
	for qid in QUERY_RANGE:
		queryQrels = dict(qrelsDict[qid])
		queryScores = baselineScores[qid]
		queryTopicModel = defaultdict(float) # TOPIC_MODEL_SCORES[qid]
		queryDoc2Vec = defaultdict(float) #DOC2VEC_SCORES[qid]
		queryClfRankings = classifierRankings[qid]
		queryClfScores = classifierScores[qid]
		
		if opts.fusion == "interpolation":
			rerankedScores = [(did, utils.interpolate(queryScores[did][1], queryClfScores[did][0], bm25Weight)) for did in queryScores.keys()]
		elif opts.fusion == "rrf":
			rerankedScores = [(did, rrf(queryScores[did][0], queryClfRankings[did], bm25Weight)) for did in queryScores.keys()]
		elif opts.fusion == "borda":
			rerankedScores = [(did, borda(queryScores[did][0], queryClfRankings[did], bm25Weight)) for did in queryScores.keys()]
						   
		rerankedScores.sort(key = lambda docScore : docScore[1], reverse = True)
		
		top10Docs = set([doc for (doc, _) in rerankedScores[:10]])
		relDocs = set([did for (did, rel) in queryQrels.items() if rel > 0])
		p10 = float(len(top10Docs & relDocs)) / 10.0
		allP10s.append(p10)
		
		judgedDocs = set(queryQrels.keys())
		unjudged += float(len(top10Docs - judgedDocs)) / 10.0
		
		if writeFile:
			rank = 1
			for did, score in rerankedScores:
				out.write("%d Q0 %s %3d %f SUMMARY" % (qid, did, rank, score))
				out.write("\t#\t%f\t%d\t%f\t%s\t%f\t%f\t\t%s\n" %
								(bm25Weight,
								queryScores[did][0],
								queryScores[did][1],
								classifierStr(queryClfScores[did]),
								queryTopicModel.get(did, -1),
								queryDoc2Vec.get(did, -1),
								qrelStr(queryQrels.get(did))))
				rank += 1
	
	if writeFile:
		out.close()
	
	if printUnjudged:
		print "Weight = %.2f Unjudged = %.2f, P10 = %.2f" % (bm25Weight, unjudged / len(QUERY_RANGE), np.mean(allP10s))
	
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
	baselineScores = utils.getBaselineScores(BASELINE_RESULTS_FILE, QUERY_RANGE)
	classifierScores = utils.getClassifierScores(CLASS_ID, opts.classifier, baselineScores, BASIC_WEIGHT, MAX_CUTOFF, DIVISION_CUTOFF)
	classifierRankings = computeClassifierRankings(baselineScores, classifierScores)
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID + "." + opts.classifier + "." + opts.fusion
 	lambdaRerank(QRELS_FILE, baselineScores, classifierScores, classifierRankings, rerankedFile)

run()

def rerankKnownWeights():
	baselineScores = utils.getBaselineScores(BASELINE_RESULTS_FILE, QUERY_RANGE)
	classifierScores = utils.getClassifierScores(CLASS_ID, opts.classifier, baselineScores, BASIC_WEIGHT, MAX_CUTOFF, DIVISION_CUTOFF)
	classifierRankings = computeClassifierRankings(baselineScores, classifierScores)
	rerankedFile = BASELINE_RESULTS_FILE + ".reranked." + CLASS_ID + "." + opts.classifier + "." + opts.fusion
	
	bm25Weight = 0.64 #weights.getBm25Weight(CLASS_ID, TARGET)
	
#	print "Weights: %.2f" % (bm25Weight, classifierWeight, topicModelWeight)
	
	p10Avg, p10List = rerankScores(bm25Weight, baselineScores, classifierScores, classifierRankings, rerankedFile, writeFile=True)
	print "%.2f" % p10Avg
#	print p10List

#rerankKnownWeights()

def getRandomClassifiers(randomClfScoresAllDocs, baselineScores, num):
	randomClassifiers = []
	for _ in range(0, num):
		randomClfDict = {}
		for qid, docScoresDict in baselineScores.items():
			docs = docScoresDict.keys()
			randomClfScores = [randomClfScoresAllDocs[doc] for doc in docs]
			randomClfScores = utils.minMaxNormalizeList(randomClfScores)
			randomClfDict[qid] = dict(zip(docs, zip(randomClfScores, randomClfScores, randomClfScores)))
		randomClassifiers.append(randomClfDict)
	return randomClassifiers

def random(randomClfScoresAllDocs, baselineResultsFile, numIter, qrelsDict=QRELS):
	baselineScores = utils.getBaselineScores(baselineResultsFile, QUERY_RANGE)
	randomClassifiers = getRandomClassifiers(randomClfScoresAllDocs, baselineScores, numIter)
	
#	print "Baseline = %.4f" % getP10(QRELS_FILE, BASELINE_RESULTS_FILE)
	
	maxP10 = 0.0
	p10List = []
	for weight in np.linspace(0,1,51):
		sumP10 = 0.0
		for i in range(0, numIter):
			p10, _ = rerankScores(weight, baselineScores, randomClassifiers[i], defaultdict(float), None, qrelsDict=qrelsDict, printUnjudged=True)
			sumP10 += p10
		avgP10 = sumP10/numIter
		p10List.append(avgP10)
		maxP10 = max(avgP10, maxP10)
#		print "%.2f %.4f" % (weight, round(avgP10, 4))
	print "MaxP10=%.4f" % maxP10
	return p10List
	
def randomAllRuns(numIter):
	qrels2014 = utils.readQrels("../data/qrels/qrels-treceval-2014.txt")
	qrels2015 = utils.readQrels("../data/qrels/qrels-treceval-2015.txt")

	maxTotal = 0.0
	maxSum2014 = 0.0
	maxDesc2014 = 0.0
	maxSum2015 = 0.0
	maxDesc2015 = 0.0
	bestWeightTotal = 0.0

	classifiedDocs = utils.readClassPredictions("Basic", "diag", False, False).keys()
	
	for it in range(numIter):
		randomClfScoresAllDocs = dict(zip(classifiedDocs, np.random.uniform(0, 1, size=len(classifiedDocs))))
		
		sum2014 = random(randomClfScoresAllDocs, "../ir/results/results-2014-sum.txt", 1, qrelsDict=qrels2014)
		desc2014 = random(randomClfScoresAllDocs, "../ir/results/results-2014-desc.txt", 1, qrelsDict=qrels2014)
		sum2015 = random(randomClfScoresAllDocs, "../ir/results/results-2015-sum.txt", 1, qrelsDict=qrels2015)
		desc2015 = random(randomClfScoresAllDocs, "../ir/results/results-2015-desc.txt", 1, qrelsDict=qrels2015)
		
		avgP10s = np.mean([sum2014, desc2014, sum2015, desc2015], axis=0)
		maxAvgP10 = max(avgP10s)
		argmax = np.argmax(avgP10s)
		bestWeight = argmax*0.02
		print "MaxWeight=%.2f MaxP10=%.4f (%.4f %.4f %.4f %.4f)" % (bestWeight, 
																	maxAvgP10, sum2014[argmax], desc2014[argmax], sum2015[argmax], desc2015[argmax])
		maxTotal += maxAvgP10
		maxSum2014 += sum2014[argmax]
		maxDesc2014 += desc2014[argmax]
		maxSum2015 += sum2015[argmax]
		maxDesc2015 += desc2015[argmax]
		bestWeightTotal += bestWeight
		
	print "%.4f --> %.4f (%.4f %.4f %.4f %.4f)" % (bestWeightTotal/numIter, 
													maxTotal/numIter, maxSum2014/numIter, maxDesc2014/numIter, maxSum2015/numIter, maxDesc2015/numIter)
	
#randomAllRuns(1)
		
		
		


