#!/bin/python

import os
import math
from scipy import stats
import subprocess
import numpy as np
import itertools
import sys

sys.path.insert(0, "../utils/")
import utils

classifier = sys.argv[1]
class_id = sys.argv[2]
#resYear = sys.argv[3]
#qrelYear = resYear[:4]

qrelsSampleEval2014 = "../data/qrels/qrels-sampleval-2014.txt"
qrelsSampleEval2015 = "../data/qrels/qrels-sampleval-2015.txt"

baseline2014 = "../ir/results/results-2014-" + class_id + ".txt"
baseline2015 = "../ir/results/results-2015-A-" + class_id + ".txt"

reranked2014 = baseline2014 + ".reranked." + classifier
reranked2015 = baseline2015 + ".reranked." + classifier

#qrel_file = "../data/qrels/qrels-treceval-" + qrelYear + ".txt"
#baseline_results_file = "../ir/results/results-" + resYear + "-" + class_id + ".txt"
#reranked_results_file = baseline_results_file + ".reranked." + classifier

eval_progname = "../eval/trec_eval.9.0/trec_eval"
perl_progname = "../eval/sample_eval.pl"

topic_offsets = {"diag": 1, "test": 11, "treat": 21}

def interpolate(x, y, w):
	return w * x + (1 - w) * y

def zscore_dict(d):
	return dict(zip(d.keys(), stats.zscore(d.values())))

def simple_rerank(weight, baselineFile, rerankedFile):
	baseline_results = utils.readResults(baselineFile)   
	class_predictions = utils.readClassPredictions(classifier, class_id)
	class_predictions = zscore_dict(class_predictions)
	reranked_results = open(rerankedFile, "w")
	topic_offset = topic_offsets[class_id]
	for topic_id in range(topic_offset, topic_offset + 10):
		doc, ranks, scores = zip(*(baseline_results[topic_id]))
		norm_scores = dict(zip(doc, stats.zscore(scores)))
		reranked = [(doc_id, interpolate(norm_scores[doc_id], class_predictions[doc_id], weight)) for doc_id in norm_scores.keys()]

		reranked.sort(key = lambda doc_score : doc_score[1], reverse = True)
		rank = 1
		for doc_id, score in reranked:
			reranked_results.write("%d Q0 %s %d %f STANDARD\n" % (topic_id, doc_id, rank, score))
			rank += 1
	reranked_results.close()

def get_precision_at(prec_num, weight, qrelsFile, baselineFile, rerankedFile):
	simple_rerank(weight, baselineFile, rerankedFile)
	output = subprocess.Popen([eval_progname, qrelsFile, rerankedFile], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	index = output.index("P_" + str(prec_num))
	return float(output[index + 2])

def get_infNDCG(weight, qrelsSampleEvalFile, baselineFile, rerankedFile):
	simple_rerank(weight, baselineFile, rerankedFile)
	output = subprocess.Popen(["perl", perl_progname, qrelsSampleEvalFile, rerankedFile], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	index = output.index("infNDCG")
	return float(output[index + 2])

def get_best_weight(measure):
	best_weight = 0.0
	measure_max = 0.0
	measure_max_2014 = 0.0
	measure_max_2015 = 0.0
	all_res = []
	for weight in np.linspace(0,1,101):
		if measure == "infNDCG":
			measure2014 = get_infNDCG(weight, qrelsSampleEval2014, baseline2014, reranked2014)
			measure2015 = get_infNDCG(weight, qrelsSampleEval2015, baseline2015, reranked2015)
		else: # measure == "Pn"
			prec_num = int(measure[1:])
			measure2014 = get_precision_at(prec_num, weight, utils.QRELS_2014, baseline2014, reranked2014)
			measure2015 = get_precision_at(prec_num, weight, utils.QRELS_2015, baseline2015, reranked2015)
		avgMeasure = 0.5 * measure2014 + 0.5 * measure2015
		print "weight = %f\tavg = %f\t2014 = %f\t2015 = %f" % (weight, avgMeasure, measure2014, measure2015)
		all_res.append((weight, avgMeasure, measure2014, measure2015))
		if avgMeasure > measure_max:
			measure_max = avgMeasure
			measure_max_2014 = measure2014
			measure_max_2015 = measure2015
			best_weight = weight
	return best_weight, measure_max, measure_max_2014, measure_max_2015, all_res

def lambda_rerank():
	best_weight, measure_max, measure_max_2014, measure_max_2015, all_res = get_best_weight("P10")
	for res in all_res:
		print "weight = %f\tavg = %f\t2014 = %f\t2015 = %f" % (res[0], res[1], res[2], res[3])
	print "\nbest weight = %f\tmax avg = %f\t2014 = %f\t2015 = %f" % (best_weight, measure_max, measure_max_2014, measure_max_2015)
	simple_rerank(best_weight, baseline2014, reranked2014)
	simple_rerank(best_weight, baseline2015, reranked2015)
	
lambda_rerank()

