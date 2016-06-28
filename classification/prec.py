import sys
import os
import numpy as np

sys.path.insert(0, "../utils/")
import utils

CLASSIFIER = sys.argv[1]
CLASS_ID = sys.argv[2]

if len(sys.argv) > 3:
	hedges=True
else:
	hedges=False

def getRelevantQrelDocIds(qrels, CLASS_ID):
	dids = []
	for qid, docRels in qrels.items():
		for did, rel in docRels:
			if rel > 0:
				if (CLASS_ID == "diag" and qid <= 10) or \
				   (CLASS_ID == "test" and qid > 10 and qid <= 20) or \
				   (CLASS_ID == "treat" and qid > 20):
					dids.append(did)
	return set(dids)

def prec(qrels, hedges):
	dids = getRelevantQrelDocIds(qrels, CLASS_ID)
#	classifiedDids = utils.readInts(os.path.join(utils.RES_AND_QRELS_DIR, "ids.txt"))
#	classifierScores = dict(zip(dids, np.random.choice([-1, 1], size=len(dids))))
	classifierScores = utils.readClassPredictions(CLASSIFIER, CLASS_ID, hedges=hedges)
	classifierScores = {did:score for did,score in classifierScores.items() if did in dids}
	good = [did for did in classifierScores.keys() if classifierScores[did] > 0]
	bad = [did for did in classifierScores.keys() if classifierScores[did] <= 0]
	print "Good/bad: ", len(good), len(bad)
	
qrels2014 = utils.readQrels2014()
qrels2015 = utils.readQrels2015()

prec(qrels2014, hedges)
prec(qrels2015, hedges)
			
