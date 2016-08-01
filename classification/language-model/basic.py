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
		return 5.5
	if CLASS_ID == "test":
		return 5.25
	else:
		return 2.0

sumDocLen = 0
for did in TO_CLASSIFY_DOC_IDS:
	docLen = LENGTHS[did]
	occ = getOccurences(did, TERMS[CLASS_ID])
#	minOcc = minOccurences(docLen)

	### TODO vary cutoff in  simplererank
	pred = occ #min(opts.max_cutoff, float(occ) / minOcc)

	out.write("%f\n" % pred)
	sumDocLen += docLen
out.close()

#print sumDocLen/len(TO_CLASSIFY_DOC_IDS)
