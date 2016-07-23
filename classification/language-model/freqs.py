import os
import sys
import codecs
import math
import re
import numpy as np
import scipy.stats
from collections import Counter, defaultdict
import matplotlib.pyplot as plt


sys.path.insert(0, "../../utils/")
import utils

CLASS_ID = sys.argv[1]
QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}

TARGETS = ["diag", "test", "physic exam", "investig", "evalu", "examin", "treat", "therap"]
#TARGETS = ["treat"]

DOC_IDS = utils.readInts("../data/res-and-qrels/ids.txt")

########### TOGGLE for writing data
LINES = codecs.open("../data/res-and-qrels/words.txt", "r", "utf-8").read().splitlines() # res-and-ALL-qrels sometimes !!
DOCS = zip(DOC_IDS, LINES)
print "read docs", len(LINES)
###########

#### TOGGLE for reading data
#LENGTHS = dict(zip(DOC_IDS, utils.readInts("word-counts/lengths.txt")))

def writeWordCountsForTarget(target):
	out = open("word-counts/" + target + ".txt", "w")
	counter = 0
	for did, text in DOCS:
		count = sum(1 for _ in re.finditer(r"\b%s" % target, text))
		out.write("%d\n" % count)
		counter += 1
		if counter % 1000 == 0:
			print counter
	out.close()
	
def writeWordCounts():
	for target in TARGETS:
		print target
		writeWordCountsForTarget(target)
		print "----"

def writeLengths():
	out = open("word-counts/lengths.txt", "w")
	for did, text in DOCS:
		out.write("%d\n" % len(text.split()))
	out.close()

writeWordCounts()
writeLengths()

COUNTS_DICT = {}
for target in TARGETS:
	COUNTS_DICT[target] = dict(zip(DOC_IDS, utils.readInts("word-counts/" + target + ".txt")))

def measure(count, did):
#	return float(count)/LENGTHS[did] * 1e3
	return count

def printFreqs(qid, dids):
	print "%s|%5d:\t" % (str(qid), len(dids)),
	allCounts = []
	for target in TARGETS:
		counts = [measure(count, did) for did, count in COUNTS_DICT[target].items() if did in dids]
		medianCount = np.median(counts)
		
#		totals[target].append(medianCount)
#		weights[target].append(len(dids))
		print "%s: %6.2f\t" % (target, medianCount),
		allCounts.append(counts)
	print
	return allCounts

def printOverallStats(totals, weights):
	print "OVR\t\t",
	for target in TARGETS:
		print "%s: %6.2f\t" % (target, np.average(totals[target], weights=weights[target])),
	print
#	print "MIN\t\t",
#	for target in TARGETS:
#		print "%s: %6.2f\t" % (target, min(totals[target])),
#	print
#	print "MAX\t\t",
#	for target in TARGETS:
#		print "%s: %6.2f\t" % (target, max(totals[target])),
#	print

def wordFreq(qrels, queryRange):
	relTotals = defaultdict(list)
	relWeights = defaultdict(list)
	nonrelTotals = defaultdict(list)
	nonrelWeights = defaultdict(list)
	allRelDocs = []
	allNonrelDocs = []
	
	for qid in queryRange:
		queryQrels = qrels[qid]
		
		relDocs = set([did for (did, rel) in queryQrels if rel > 0])
		relCounts = printFreqs(qid, relDocs)
		
		nonrelDocs = set([did for (did, rel) in queryQrels if rel == 0])
		nonrelCounts = printFreqs(qid, nonrelDocs)
		
#		plt.hist(relCounts[0], bins=50, histtype='step')
#		plt.hist(nonrelCounts[0], bins=50, histtype='step')
#		plt.show()
		
		print "-" * 170
		
		allRelDocs += relDocs
		allNonrelDocs += nonrelDocs
	
	allRelDocs = set(allRelDocs)
	allNonrelDocs = set(allNonrelDocs)
	allNonrelDocs -= allRelDocs
	
	print "=" * 170
	allRelCounts = printFreqs("ALL", allRelDocs)
#	printOverallStats(relTotals, relWeights)

	print "-" * 170
	allNonrelCounts = printFreqs("ALL", allNonrelDocs)
#	plt.hist(allRelCounts[0], bins=50, histtype='step')
#	plt.hist(allNonrelCounts[0], bins=50, histtype='step')
#	plt.show()
#	printOverallStats(nonrelTotals, nonrelWeights)
	
	print "=" * 170
	print
	

#QRELS_2014 = utils.readQrels2014()
#QRELS_2015 = utils.readQrels2015()
#QUERY_RANGE = range(QUERY_OFFSETS[CLASS_ID], QUERY_OFFSETS[CLASS_ID] + 10)
#wordFreq(QRELS_2014, QUERY_RANGE)
#wordFreq(QRELS_2015, QUERY_RANGE)
		
	
