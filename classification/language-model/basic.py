import os
import sys
import codecs
import math
import re
from optparse import OptionParser

sys.path.insert(0, "../../utils/")
import utils

CLASS_ID = sys.argv[1]

op = OptionParser()
op.add_option("--division_cutoff",
			  action="store", type=float, default=-1.0,
			  help="division cutoff.")
op.add_option("--max_cutoff",
			  action="store", type=float, default=2.0,
			  help="max cutoff.")

(opts, args) = op.parse_args()


TARGETS = ["diag", "test", "physic exam", "investig", "evalu", "examin", "treat", "therap"]
TERMS = {"diag" : ["diag"], "test": ["diag", "test"], "treat":["treat"]}#, "therap"]}

TO_CLASSIFY_DOC_IDS = utils.readInts("../data/res-and-qrels/ids.txt")
DOC_IDS = utils.readInts("../data/res-and-qrels/ids.txt")
LENGTHS = dict(zip(DOC_IDS, utils.readInts("word-counts/lengths.txt")))

#docs = codecs.open("../data/res-and-qrels/words.txt", "r", "utf-8").read().splitlines()

COUNTS_DICT = {}
for target in TARGETS:
	COUNTS_DICT[target] = dict(zip(DOC_IDS, utils.readInts("word-counts/" + target + ".txt")))

out = open("../data/res-and-qrels/results/" + CLASS_ID + "/results.txt.Basic", "w")

def getOccurences(did, words):
	s = 0.0
	for word in words:
		s += COUNTS_DICT[word][did]
	return s

def minOccurences(docLen):
	if opts.division_cutoff > 0:
		return opts.division_cutoff

	if CLASS_ID == "diag":
		return 5.75
#		return min(4, math.ceil(docLen/200.0))
	if CLASS_ID == "test":
		#if docLen < 400:
			#return min(2, math.ceil(docLen/100.0))
		#return min(4.5, math.ceil(docLen/200.0))
		return 5.25
	else:
		return 18.25 #2.0 #3#max(1, math.log10(docLen))

sumDocLen = 0
for did in TO_CLASSIFY_DOC_IDS:
	docLen = LENGTHS[did]
	occ = getOccurences(did, TERMS[CLASS_ID])
	minOcc = minOccurences(docLen)
#	if CLASS_ID == "diag":
#		freq = float(occ)/docLen * 1e3
#		pred = freq/3

	pred = min(opts.max_cutoff, float(occ) / minOcc)
#	if CLASS_ID == "treat":
#		if occ > 9:
#			pred = 2
	
#	if CLASS_ID == "test" and "case report" in doc:
#		pred += 5
#	pred = min(3, math.log(1 + float(occ) / (minOcc + 1)))
	out.write("%f\n" % pred)
	sumDocLen += docLen
out.close()

#print sumDocLen/len(TO_CLASSIFY_DOC_IDS)
