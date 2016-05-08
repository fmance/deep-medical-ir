#!/bin/python

import os, math
from random import randint
from scipy import stats
import subprocess
import numpy as np
import pprint
import itertools
import random
import sys

from rankpy.queries import Queries
from rankpy.queries import find_constant_features

from rankpy.models import LambdaMART
import logging


class_id = sys.argv[1]

#classifier = ""
classifier = ".SGDClassifier"
#classifier = ".MultinomialNB"

resYear = sys.argv[2]
qrelYear = resYear[:4]

qrel_file = "../data/qrels/qrels-treceval-" + qrelYear + ".txt"
baseline_results_file = "../ir/results/results-" + resYear + "-" + class_id + ".txt"
reranked_results_file = baseline_results_file + ".reranked" + classifier
eval_progname = "../eval/trec_eval.9.0/trec_eval"

topic_offsets = {"diag": 1, "test": 11, "treat": 21}

def read_baseline_results(res_file):
    results = {}
    
    for line in open(res_file):
        parts = line.split()
        topic_id = int(parts[0])
        doc_id = int(parts[2])
        score = float(parts[4])
        if (topic_id in results):
            results[topic_id].append((doc_id, score))
        else:
            results[topic_id] = [(doc_id, score)]
    return results

def read_class_predictions_nn():
    doc_ids = map(lambda did: int(did), open("../data/nn/" + class_id + "/res/ids.txt").read().split())
    predictions = {}
    i = 0
    for line in open("res/" + class_id + "/predictions-on-ir-res.txt"):
        parts = line.split()
        predictions[doc_ids[i]] = float(parts[1]) - float(parts[2])
        i += 1
    return predictions

def read_class_predictions_non_nn():
    doc_ids = map(lambda did: int(did), open("../classification/data/ir-res/ids.txt").read().split())
    predictions = {}
    i = 0
    for line in open("../classification/data/" + class_id + "/predictions-on-ir-res.txt" + classifier):
        parts = line.split()
        pred = int(parts[0])
        if pred == 1: #!!!!#
            predictions[doc_ids[i]] = 1
        else:
            predictions[doc_ids[i]] = -1
        i += 1
    return predictions

def interpolate(x, y, w):
    return w * x + (1 - w) * y #*(randint(0,10) < 7)

def zscore_dict_of_pairs(d):
    k, v = zip(*d.items())
    flat_v = list(itertools.chain(*v))
    flat_v = stats.zscore(flat_v)
    it = iter(flat_v)
    v = zip(it, it)
    return dict(zip(k, v))

def zscore_dict(d):
    return dict(zip(d.keys(), stats.zscore(d.values())))

def simple_rerank(weight):
    baseline_results = read_baseline_results(baseline_results_file)   
    class_predictions = read_class_predictions_non_nn()
    class_predictions = zscore_dict(class_predictions)
    reranked_results = open(reranked_results_file, "w")
    topic_offset = topic_offsets[class_id]
    for topic_id in range(topic_offset, topic_offset + 10):
        doc, scores = zip(*(baseline_results[topic_id]))
        norm_scores = dict(zip(doc, stats.zscore(scores)))
        reranked = [(doc_id, interpolate(norm_scores[doc_id], class_predictions[doc_id], weight)) for doc_id in norm_scores.keys()]

        #norm_scores = dict(baseline_results[topic_id])
        #reranked = [(doc_id, norm_scores[doc_id] + weight * class_predictions[doc_id]) for doc_id in norm_scores.keys()]

        reranked.sort(key = lambda doc_score : doc_score[1], reverse = True)
        rank = 1
        for doc_id, score in reranked:
            reranked_results.write("%d Q0 %s %d %f STANDARD\n" % (topic_id, doc_id, rank, score))
            rank += 1
    reranked_results.close()

def get_precision_at(prec_num, weight):
    simple_rerank(weight)
    output = subprocess.Popen([eval_progname, qrel_file, reranked_results_file], stdout=subprocess.PIPE).communicate()[0]
    output = output.split()
    index = output.index("P_" + str(prec_num))
    return float(output[index + 2])

def get_best_weight(prec_num):
    best_weight = 0.0
    prec_max = 0.0
    all_res = []
    for weight in np.linspace(0,1,101):
        prec = get_precision_at(prec_num, weight)
        all_res.append((weight, prec))
        if prec > prec_max:
            prec_max = prec
            best_weight = weight
    return best_weight, prec_max, all_res

def lambda_rerank():
    best_weight, prec_max, all_res = get_best_weight(10)
    for res in all_res:
        print "%g %g" % (res[0], res[1])
    print "\nbest weight %g prec = %g" % (best_weight, prec_max)
    simple_rerank(best_weight)
    
lambda_rerank()

