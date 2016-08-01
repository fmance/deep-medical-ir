import os
import sys
from optparse import OptionParser
from collections import defaultdict
import subprocess

sys.path.insert(0, "../utils/")
import utils

CLASS_ID = sys.argv[1]
TARGET = sys.argv[2]
YEAR = TARGET[:4]
QRELS_FILE = "../data/qrels/qrels-treceval-" + YEAR + ".txt"
EVAL_PROGNAME = "../eval/trec_eval.9.0/trec_eval"

op = OptionParser()
op.add_option("--previous_fusion",
			  action="store", default="interpolation",
			  help="fusion method.")
op.add_option("--fusion",
			  action="store", default="rrf",
			  help="fusion method.")

(opts, args) = op.parse_args()

CLASSIFIERS = [
	"Basic",
	"BernoulliNB",
	"MultinomialNB",
	"NearestCentroid",
	"PassiveAggressiveClassifier.hinge",
	"Perceptron",
	"RidgeClassifier",
	"RandomForestClassifier",
	"LinearSVC.squared_hinge.l2",
	"SGDClassifier.log.l2",
	"SGDClassifier.log.elasticnet",
	"SGDClassifier.hinge.l2",
	"SGDClassifier.hinge.elasticnet",
	"SGDClassifier.squared_hinge.l2",
	"SGDClassifier.squared_hinge.elasticnet",
	"SGDClassifier.squared_loss.l2",
	"SGDClassifier.squared_loss.elasticnet",
	"SGDClassifier.epsilon_insensitive.l2",
	"SGDClassifier.epsilon_insensitive.elasticnet",
	"Pipeline.epsilon_insensitive.l2",
	"SVMPerf",
	"NN"
]

def rrfFiles(outputFile):
	ranksPerQuery = defaultdict(list)
	for clf in CLASSIFIERS:
		resFile = os.path.join(utils.IR_RESULTS_DIR, "results-" + TARGET + ".txt.reranked." + CLASS_ID + "." + clf + "." + opts.previous_fusion)
#		print "Reading " + resFile
		res = utils.readResults(resFile)
		for qid, docRankScores in res.items():
			docs, ranks, scores = zip(*docRankScores)
			ranksPerQuery[qid].append(dict(zip(docs, ranks)))
	
	out = open(outputFile, "w")
	for qid in sorted(ranksPerQuery.keys()):
		scores = defaultdict(float)
		rankList = ranksPerQuery[qid]
		for ranking in rankList:
			for did, rank in ranking.items():
				if opts.fusion == "rrf":
					scores[did] += 1.0 / (60.0 + rank)
				elif opts.fusion == "borda":
					scores[did] += rank

		if opts.fusion == "borda":
			scores = {did: 1.0/float(score) for did, score in scores.items()}
							
		scores = scores.items()
		scores.sort(key = lambda docScore : docScore[1], reverse = True)
		rank = 1
		for did, score in scores:
			out.write("%d Q0 %s %3d %f SUMMARY\n" % (qid, did, rank, score))
			rank += 1
	out.close()

def getP10(qrelsFile, resultsFile):
	output = subprocess.Popen([EVAL_PROGNAME, qrelsFile, resultsFile], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	index = output.index("P_10")
	return float(output[index + 2])
	
RESULTS_FUSED = os.path.join(utils.IR_RESULTS_DIR, "results-" + TARGET + ".txt.reranked." + CLASS_ID + "." +
								opts.previous_fusion + ".ALL_CLASSIFIERS_FUSED_BY_" + opts.fusion.upper())
rrfFiles(RESULTS_FUSED)

print getP10(QRELS_FILE, RESULTS_FUSED)


		
		
		
	
	
