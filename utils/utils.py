#!/bin/python

import os
import shutil
from collections import defaultdict
import numpy

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
IR_RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ir/results/"))

RESULTS_2014 = os.path.join(IR_RESULTS_DIR, "results-2014.txt")
RESULTS_2015_A = os.path.join(IR_RESULTS_DIR, "results-2015.txt")
RESULTS_2015_B = os.path.join(IR_RESULTS_DIR, "results-2015-B-BM25_Lucene.txt")
#BM25_SCORES_2014 = os.path.join(IR_RESULTS_DIR, "bm25-scores-2014.txt")
#BM25_SCORES_2015 = os.path.join(IR_RESULTS_DIR, "bm25-scores-2015.txt")
#TFIDF_SCORES_2014 = os.path.join(IR_RESULTS_DIR, "tfidf-scores-2014.txt")
#TFIDF_SCORES_2015 = os.path.join(IR_RESULTS_DIR, "tfidf-scores-2015.txt")

CLASSIFICATION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../classification"))

QRELS_DIR = os.path.join(DATA_DIR, "qrels")
QRELS_2014 = os.path.join(QRELS_DIR, "qrels-treceval-2014.txt")
QRELS_2015 = os.path.join(QRELS_DIR, "qrels-treceval-2015.txt")

QUERIES_DIR = os.path.join(DATA_DIR, "queries")
PLAINTEXT_DIR = os.path.join(DATA_DIR, "plaintext")
RES_AND_QRELS_DIR = os.path.join(CLASSIFICATION_DIR, "data", "res-and-qrels")

def readInts(intsFile):
	return map(int, open(intsFile).read().split())

VALID_DOC_IDS = set(readInts(os.path.join(DATA_DIR, "doc-ids/valid-doc-ids.txt")))

LONG_DOC_IDS_PATH = os.path.join(DATA_DIR, "doc-ids/long-doc-ids.txt")
LONG_DOC_IDS = set(readInts(LONG_DOC_IDS_PATH))

def readQrels(qrelFile):
	qrels = defaultdict(list)
	for line in open(qrelFile):
		parts = line.split()
		qid = int(parts[0])
		did = int(parts[2])
		rel = int(parts[3])
		if did in VALID_DOC_IDS:
			qrels[qid].append((did, rel))
	return qrels

def readQrels2014():
	return readQrels(QRELS_2014)

def readQrels2015():
	return readQrels(QRELS_2015)

def getQrelsDocIds(qrels):
	return [did for (_, docRelPairList) in qrels.items() for (did, _) in docRelPairList]

def getRelevantQrelDocIdsForCategory(qrels, category):
	dids = []
	for qid, docRels in qrels.items():
		for did, rel in docRels:
			if rel > 0:
				if (category == "diag" and qid <= 10) or \
				   (category == "test" and qid > 10 and qid <= 20) or \
				   (category == "treat" and qid > 20):
					dids.append(did)
	return set(dids)

def getRelevantQrelDocIdsAllCategories(qrels):
	dids = []
	for qid, docRels in qrels.items():
		for did, rel in docRels:
			if rel > 0:
				dids.append(did)
	return set(dids)

def readResults(resultsFile):
	results = defaultdict(list)
	for line in open(resultsFile):
		parts = line.split()
		qid = int(parts[0])
		did = int(parts[2])
		rank = int(parts[3])
		score = float(parts[4])
		if did in VALID_DOC_IDS:
			results[qid].append((did, rank, score))
	return results

def readResults2014():
	return readResults(RESULTS_2014)

def readResults2015A():
	return readResults(RESULTS_2015_A)

def readResults2015B():
	return readResults(RESULTS_2015_B)

def readResultsAllModels(year):
	scores = []
	models = ["", "-sep"]
	if year == 2014:
		models += ["-expanded", "-expanded-sep"]
	for model in models:
		scoreFile = os.path.join(IR_RESULTS_DIR, "results-" + str(year) + model + ".txt")
		scores.append(readResults(scoreFile))
	return scores

def getResultsDocIds(results):
	return [did for (_, docResList) in results.items() for (did, _, _) in docResList]

def getFilePaths(filenames, rootDir):
	print "Getting %d filepaths from %s" % (len(filenames), rootDir)
	filenames = set(filenames)
	paths = {}
	for root, dirs, files in os.walk(rootDir):
		matchingFiles = filenames & set(files)
		for fname in matchingFiles:
			paths[fname] = os.path.join(root, fname)
	print "Found %d files in %s" % (len(paths), rootDir)
	return paths

def copyFiles(filepaths, destDir):
	print "Copying %d files to %s" % (len(filepaths), destDir)
	counter = 0
	for path in filepaths:
		shutil.copy(path, destDir)
		counter += 1
		if counter % 10000 == 0:
			print "Copied %d files" % counter

def getAndCopyFiles(filenames, srcRootDir, destDir):
	pathsDict = getFilePaths(filenames, srcRootDir)
	copyFiles(pathsDict.values(), destDir)

def maxNormalize(ls):
	m = max(ls)
	return [float(x)/m for x in ls]

def readClassPredictions(classifier, classId, hedges=False):
	if classId == "test":
		classId = "diag"
	docIds = readInts(os.path.join(RES_AND_QRELS_DIR, "ids.txt"))
	hedgesPart = "-hedges" if hedges else ""
	results = map(float, open(os.path.join(RES_AND_QRELS_DIR + hedgesPart, "results", classId, "results.txt." + classifier)).read().split())
	
#	if classifier == "NN":
#		results = map(numpy.sign, results)
	
	if classifier != "NN":
		results = map(lambda x : 2*x-1, results) # transform 1 to 1 and 0 to -1
	
	return dict(zip(docIds, results))
