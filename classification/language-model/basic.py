import os
import sys
import codecs
import math

sys.path.insert(0, "../../utils/")
import utils

CLASS_ID = sys.argv[1]

TERMS = {"diag" : ["diag"], "treat":["treat", "therap"]}

docIds = utils.readInts("../data/res-and-qrels/ids.txt")
docs = codecs.open("../data/res-and-qrels/words.txt", "r", "utf-8").read().splitlines()

out = open("../data/res-and-qrels/results/" + CLASS_ID + "/results.txt.Basic", "w")

def getOccurences(text, words):
	s = 0
	for word in words:
		s += text.count(word)
	return s

def minOccurences(docLen):
	if CLASS_ID == "diag":
		return 4
	else:
		return 3#max(1, math.log10(docLen))

for doc in docs:
	docLen = len(doc.split())
	if getOccurences(doc, TERMS[CLASS_ID]) > minOccurences(docLen):
		pred = 1
	else:
		pred = 0
	out.write("%f\n" % pred)
	
out.close()
