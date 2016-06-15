#!/bin/python

import os
import math
from scipy import stats
import subprocess
import numpy as np
import itertools
import sys
import pprint

sys.path.insert(0, "../utils/")
import utils

classifier = sys.argv[1]
class_id = sys.argv[2]
year = sys.argv[3]

qrelsSampleEval = "../data/qrels/qrels-sampleval-" + year + ".txt"
qrelsTrecEval = "../data/qrels/qrels-treceval-" + year + ".txt"
baselineResultsFile = "../ir/results/results-" + year + "-" + class_id + ".txt"
rerankedFile = baselineResultsFile + ".reranked." + classifier

eval_progname = "../eval/trec_eval.9.0/trec_eval"
perl_progname = "../eval/sample_eval.pl"

topic_offsets = {"diag": 1, "test": 11, "treat": 21}

def interpolate(x, y, w):
	if y == None:
		return x
	else:
		return w * x + (1 - w) * y

def zscore_dict(d):
	return dict(zip(d.keys(), stats.zscore(d.values())))

class_predictions = utils.readClassPredictions(classifier, class_id)
class_predictions = zscore_dict(class_predictions)
baselineResults = utils.readResults(baselineResultsFile)

topic_offset = topic_offsets[class_id]

def getNormScores(baselineResults):
	normScores = {}
	for topic_id in range(topic_offset, topic_offset + 10):
		doc, _, scores = zip(*(baselineResults[topic_id]))
		normScores[topic_id] = dict(zip(doc, stats.zscore(scores)))
	return normScores

baselineNormScores = getNormScores(baselineResults)

def simple_rerank(weight, baselineNormScores, rerankedFile):
	reranked_results = open(rerankedFile, "w")
	for topic_id in range(topic_offset, topic_offset + 10):
		norm_scores = baselineNormScores[topic_id]
		reranked = [(doc_id, interpolate(norm_scores[doc_id], class_predictions.get(doc_id), weight)) for doc_id in norm_scores.keys()]

		reranked.sort(key = lambda doc_score : doc_score[1], reverse = True)
		rank = 1
		for doc_id, score in reranked:
			reranked_results.write("%d Q0 %s %d %f STANDARD\n" % (topic_id, doc_id, rank, score))
			rank += 1
	reranked_results.close()

def get_precision_at(prec_num, qrelsFile, rerankedFile):
	output = subprocess.Popen([eval_progname, qrelsFile, rerankedFile], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	index = output.index("P_" + str(prec_num))
	return float(output[index + 2])

def get_infNDCG(weight, qrelsSampleEvalFile, baselineNormScores, rerankedFile):
	simple_rerank(weight, baselineNormScores, rerankedFile)
	output = subprocess.Popen(["perl", perl_progname, qrelsSampleEvalFile, rerankedFile], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	index = output.index("infNDCG")
	return float(output[index + 2])

def getBestWeights(measure, qrelsTrecEval, qrelsSampleEval, baselineNormScores, rerankedResultsFile):
	weightMap = []
	maxVal = 0.0
	for weight in np.linspace(0.2,1,41):
		if measure == "infNDCG":
			currVal = get_infNDCG(weight, qrelsSampleEval, baselineNormScores, rerankedResultsFile)
		else: # measure == "Pn"
			precNum = int(measure[1:])
			simple_rerank(weight, baselineNormScores, rerankedResultsFile)
			currVal = get_precision_at(precNum, qrelsTrecEval, rerankedResultsFile)
		maxVal = max(maxVal, currVal)
		weightMap.append((weight, currVal))
		print "%f" % (currVal),
	
	return maxVal, [weight for (weight, val) in weightMap if val == maxVal], weightMap


def lambdaRerank(measure):
	maxVal, weights, weightMap = getBestWeights(measure, qrelsTrecEval, qrelsSampleEval, baselineNormScores, rerankedFile)
	print "Max%s=%f" % (measure, maxVal),
	print "Weights=%.2f-%.2f" % (min(weights), max(weights)),
#	pprint.pprint(weights)
	simple_rerank(weights[0], baselineNormScores, rerankedFile)
	return weightMap

def rerankWithWeights():
	bestAvgWeight = {"diag":0.64, "test":1.0, "treat":0.64}
	weight = bestAvgWeight[class_id]
	print "Weights=%.2f %.2f" % (weight, weight)
	simple_rerank(weight, baselineNormScores, rerankedFile)
	
lambdaRerank("P10")
#rerankWithWeights()
