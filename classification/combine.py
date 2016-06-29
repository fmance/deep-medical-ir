import os
import sys
from collections import defaultdict

sys.path.insert(0, "../utils/")
import utils

CLASS_ID = sys.argv[1]

CLASSIFIERS = [
	"Basic",
#	"LinearSVC.squared_hinge.l2", 
#	"SGDClassifier.hinge.l2",
#	"SGDClassifier.hinge.elasticnet",
#	"SGDClassifier.squared_loss.l2",
#	"SGDClassifier.squared_loss.elasticnet",
#	"SGDClassifier.epsilon_insensitive.l2",
	"SGDClassifier.epsilon_insensitive.elasticnet",
#	"Pipeline.epsilon_insensitive.l2"
]

def combineClassifierScores():
	scores = defaultdict(float)
	for classifier in CLASSIFIERS:
		for did, score in utils.readClassPredictions(classifier, CLASS_ID, False).items():
			scores[did] += score
	return {did: score/len(CLASSIFIERS) for did, score in scores.items()}
#	return zscoreDictValues(scores)

def writeScores(scores):
	docIds = utils.readInts(os.path.join(utils.RES_AND_QRELS_DIR, "ids.txt"))
	out = open(os.path.join(utils.RES_AND_QRELS_DIR, "results", CLASS_ID, "results.txt.Combined"), "w")
	for did in docIds:
		out.write("%f\n" % (scores[did]))
	out.close()
	
writeScores(combineClassifierScores())
