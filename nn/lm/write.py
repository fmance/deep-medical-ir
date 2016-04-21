#!/bin/python

import itertools
import random

QRELS_2014 = "../../data/qrels-treceval-2014.txt"
QRELS_2015 = "../../data/qrels-treceval-2015.txt"

RESULTS_2014 = "../../data/results-2014.txt"
RESULTS_2015 = "../../data/results-2015-A.txt"

FEATURES_2014 = "../stats/features-2014.txt"
FEATURES_2015 = "../stats/features-2015.txt"

QRELS_2014_FEATURES = "qrels-2014-features.txt"
QRELS_2015_FEATURES = "qrels-2015-features.txt"

RESULTS_2014_FEATURES = "results-2014-features.txt"
RESULTS_2015_FEATURES = "results-2015-features.txt"

validDocIds = set(map(int, open("../../data/valid-doc-ids.txt").read().split()))

def readQueryDocRelevancesFromQrels(qrelsFile):
    result = {}
    for qrel in open(qrelsFile):
        parts = qrel.split()
        qid = int(parts[0])
        did = int(parts[2])
        rel = int(parts[3])
        if did in validDocIds:
            result[(qid, did)] = int(rel > 0)
    return result

def readQueryDocRelevancesFromResults(resultsFile):
    result = {}
    for line in open(resultsFile):
        parts = line.split()
        qid = int(parts[0])
        did = int(parts[2])
        result[(qid, did)] = 0
    return result

def readFeatures(featureFile):
    features = {}
    for line in open(featureFile):
        parts = line.split()
        qid = int(parts[0])
        did = int(parts[1])
        features[(qid, did)] = map(float, parts[2:])
    return features

def writeFeatureFile(queryDocRelevances, queryDocFeatures, queryOffset, outFile):
    out = open(outFile, "w")
    qdout = open(outFile + ".ids", "w")
    queryDocRelevancesList = sorted(queryDocRelevances.items(), key=lambda item:item[0][0])
    for (qid, did), relevance in queryDocRelevancesList:
        features = queryDocFeatures[(qid, did)]
        out.write("%d qid:%d " % (relevance, qid + queryOffset))
        numberedFeatures = map(lambda (fid, fval): str(fid) + ":" + str(fval), enumerate(features, 1))
        out.write(" ".join(numberedFeatures))
        out.write("\n")
        qdout.write("%d %d\n" % (qid + queryOffset, did))
    out.close()

#qrels2014 = readQueryDocRelevancesFromQrels(QRELS_2014)
qrels2015 = readQueryDocRelevancesFromQrels(QRELS_2015)
#results2014 = readQueryDocRelevancesFromResults(RESULTS_2014)
results2015 = readQueryDocRelevancesFromResults(RESULTS_2015)
#features2014 = readFeatures(FEATURES_2014)
features2015 = readFeatures(FEATURES_2015)

#writeFeatureFile(qrels2014, features2014, 0, QRELS_2014_FEATURES)
writeFeatureFile(qrels2015, features2015, 100, QRELS_2015_FEATURES)
#writeFeatureFile(results2014, features2014, 0, RESULTS_2014_FEATURES)
writeFeatureFile(results2015, features2015, 100, RESULTS_2015_FEATURES)


