#!/bin/python

import os
import shutil
from collections import defaultdict
import numpy
import json
import scipy.stats


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
VALID_DOC_IDS_2016 = set(readInts(os.path.join(DATA_DIR, "doc-ids/valid-doc-ids-2016.txt")))

LONG_DOC_IDS_PATH = os.path.join(DATA_DIR, "doc-ids/long-doc-ids.txt")
LONG_DOC_IDS = set(readInts(LONG_DOC_IDS_PATH))

def readQrels(qrelFile):
	if "2016" in qrelFile:
		return defaultdict(defaultdict)

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
		if did in VALID_DOC_IDS or "2016" in resultsFile:
			results[qid].append((did, rank, score))
	return results

#res2016Notes = readResults(os.path.join(IR_RESULTS_DIR, "results-2016-exp-note.txt"))
#out = open(os.path.join(IR_RESULTS_DIR, "results-2016-exp-note.txt.1"), "w")
#for qid, docScores in res2016Notes.items():
#	for did, rank, score in docScores:
#		out.write("%d Q0 %s %d %f ETHNote\n" % (qid, did, rank+1, score))
#out.close()

def readResults2014():
	return readResults(RESULTS_2014)

def readResults2015A():
	return readResults(RESULTS_2015_A)

def readResults2015B():
	return readResults(RESULTS_2015_B)

def readResultsAllModels(year):
	scores = []
	if year == 2016:
		models = ["-exp-sum", "-exp-desc", "-exp-note"]
	else:
		models = ["-sum", "-desc", "-exp-sum", "-exp-desc"]
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
	M = max(ls)
	return [float(x)/M for x in ls]

def readClassPredictions(classifier, classId, useDiagForTest, hedges=False):
	if classId == "test" and useDiagForTest:
		classId = "diag"
	docIds = readInts(os.path.join(RES_AND_QRELS_DIR, "ids.txt"))
	hedgesPart = "-hedges" if hedges else ""
	results = map(float, open(os.path.join(RES_AND_QRELS_DIR + hedgesPart, "results", classId, "results.txt." + classifier)).read().split())
	
#	if classifier == "NN":
#		results = map(numpy.sign, results)
	
#	if classifier != "NN":
#		results = map(lambda x : 2*x-1, results) # transform 1 to 1 and 0 to -1
	
	return dict(zip(docIds, results))
	
def writeFilteredTopicModels(target, outFile):
	res = {}
	scoreDict = json.load(open(os.path.join(CLASSIFICATION_DIR, "data", "topic-models", "queryresults" + target + ".json")))
	scoreDict = {int(qid) : docScores for qid, docScores in scoreDict.items()}
	classifiedDocIds = set(readInts(os.path.join(RES_AND_QRELS_DIR, "ids.txt")))
	
#	print [(did, score) for did, score in scoreDict[1] if did == "3361318"]
	
	out = open(outFile, "w")
	for qid in sorted(scoreDict.keys()):
		dids, scores = zip(*scoreDict[qid])
		dids = map(int, dids)
		scores = map(float, scores)
		normScores = zip(dids, scores)
		for did, score in normScores:
			if did in classifiedDocIds:
				out.write("%d %d %f\n" % (qid, did, score))
	out.close()
	
#TARGET_TYPE = "note" # sum or desc or note
#writeFilteredTopicModels("2014-" + TARGET_TYPE, os.path.join(CLASSIFICATION_DIR, "data", "topic-models", "scores-2014-" + TARGET_TYPE + "-filtered.txt"))
#writeFilteredTopicModels("2015-" + TARGET_TYPE, os.path.join(CLASSIFICATION_DIR, "data", "topic-models", "scores-2015-" + TARGET_TYPE + "-filtered.txt"))
#writeFilteredTopicModels("2016-" + TARGET_TYPE, os.path.join(CLASSIFICATION_DIR, "data", "topic-models", "scores-2016-" + TARGET_TYPE + "-filtered.txt"))

def writeResultsFromJson(target):
	bm25Res = readResults(os.path.join(IR_RESULTS_DIR, "results-" + target + ".txt"))
	jsonFile = os.path.join(CLASSIFICATION_DIR, "data", "topic-models", "queryresults" + target.replace("-exp", "") + ".json") 
	scoreDict = json.load(open(jsonFile))
	scoreDict = {int(qid) : docScores for qid, docScores in scoreDict.items()}
	out = open(os.path.join(IR_RESULTS_DIR, "results-" + target + "-lda.txt"), "w")
	for qid in sorted(scoreDict.keys()):
		dids, scores = zip(*scoreDict[qid])
		dids = map(int, dids)
		scores = map(float, scores)
		docScores = zip(dids, scores)
		
		bm25DidsForQuery = set([did for (did, _, _) in bm25Res[qid]])
		docScores = [(did, score) for did, score in docScores if did in bm25DidsForQuery]

		docScores = sorted(docScores, key=lambda ds:ds[1], reverse=True)
		rank = 1
		for did, score in docScores:#[:100]:
			out.write("%d Q0 %s %d %f STANDARD\n" % (qid, did, rank, score))
			rank += 1
	out.close()

#writeResultsFromJson("2014-sum")
#writeResultsFromJson("2015-sum")
#writeResultsFromJson("2014-desc")
#writeResultsFromJson("2015-desc")

def readTopicModels(target):
	allScores = defaultdict(list)
	for line in open(os.path.join(CLASSIFICATION_DIR, "data", "topic-models", "scores-" + target + "-filtered.txt")):
		parts = line.split()
		qid = int(parts[0])
		did = int(parts[1])
		score = float(parts[2])
		allScores[qid].append((did, score))

	res = {}
	for qid in sorted(allScores.keys()):
		dids, scores = zip(*allScores[qid])
#		scores = maxNormalize(scores)
#		scores = scipy.stats.zscore(scores)
		res[qid] = dict(zip(dids, scores))
	return res
	
def readDoc2VecScores(target):
	allScores = defaultdict(list)
	for line in open(os.path.join(CLASSIFICATION_DIR, "data", "doc2vec", "scores-" + target + ".txt")):
		parts = line.split()
		qid = int(float(parts[0]))
		did = int(float(parts[1]))
		score = float(parts[2])
		allScores[qid].append((did, score))

	res = {}
	for qid in sorted(allScores.keys()):
		dids, scores = zip(*allScores[qid])
#		scores = maxNormalize(scores)
#		scores = scipy.stats.zscore(scores)
		res[qid] = dict(zip(dids, scores))
	return res
