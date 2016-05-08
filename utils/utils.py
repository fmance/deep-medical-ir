#!/bin/python

import os
import shutil
from collections import defaultdict

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
IR_RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ir/results/"))

QRELS_DIR = os.path.join(DATA_DIR, "qrels")
QUERIES_DIR = os.path.join(DATA_DIR, "queries")
PLAINTEXT_DIR = os.path.join(DATA_DIR, "plaintext")

def readDocIds(idsFile):
	return map(int, open(idsFile).read().split())

VALID_DOC_IDS = set(readDocIds(os.path.join(DATA_DIR, "doc-ids/valid-doc-ids.txt")))

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
	return readQrels(os.path.join(QRELS_DIR, "qrels-treceval-2014.txt"))

def readQrels2015():
	return readQrels(os.path.join(QRELS_DIR, "qrels-treceval-2015.txt"))

def getQrelsDocIds(qrels):
	return [did for (_, docRelPairList) in qrels.items() for (did, _) in docRelPairList]

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
	return readResults(os.path.join(IR_RESULTS_DIR, "results-2014.txt"))

def readResults2015A():
	return readResults(os.path.join(IR_RESULTS_DIR, "results-2015-A.txt"))

def readResults2015B():
	return readResults(os.path.join(IR_RESULTS_DIR, "results-2015-B.txt"))

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

