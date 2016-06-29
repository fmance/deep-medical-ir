import os
import sys
import subprocess

sys.path.insert(0, "../utils/")
import utils

trecEval = "../eval/trec_eval.9.0/trec_eval"

CLASS_ID = sys.argv[1]
YEAR = sys.argv[2]

QRELS = "../data/qrels/qrels-treceval-" + YEAR + ".txt"
RESULTS = "../ir/results/results-" + YEAR + ".txt"
RESULTS_RERANKED = RESULTS + ".reranked." + CLASS_ID

QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]
QUERY_RANGE = range(QUERY_OFFSET, QUERY_OFFSET + 10)

def getPrecsPerQuery(precNum, results):
	output = subprocess.Popen([trecEval, "-q", QRELS, results], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	
	precMap = {}
	for i in range(0, len(output)):
		if output[i] == precNum and output[i+1] != "all":
			qid = int(output[i+1])
			prec = float(output[i+2])
			precMap[qid] = prec
	
	return precMap
	
def getMovement(qrels, res, resReranked):
	relTop10 = set([did for (did, rank, score) in res if qrels.get(did) > 0 and rank <= 10])
	relRerankedTop10 = set([did for (did, rank, score) in resReranked if qrels.get(did) > 0 and rank <= 10])
	up = relRerankedTop10 - relTop10
	down = relTop10 - relRerankedTop10
	return up, down

precs = getPrecsPerQuery("P_10", RESULTS)
precsReranked = getPrecsPerQuery("P_10", RESULTS_RERANKED)

sumPrec = 0.0
sumPrecReranked = 0.0
sumUp = 0
sumDown = 0

qrels = utils.readQrels(QRELS)
results = utils.readResults(RESULTS)
resultsReranked = utils.readResults(RESULTS_RERANKED)

for qid, prec in precs.items():
	if qid in QUERY_RANGE:
		queryQrels = dict(qrels[qid])
		queryRes = results[qid]
		queryResRer = resultsReranked[qid]
		up, down = getMovement(queryQrels, queryRes, queryResRer)
		print "%d\t%.2f\t%.2f\t" % (qid, prec, precsReranked[qid]),
		if precsReranked[qid] != prec:
			print "%+.2f" % (precsReranked[qid] - prec),
		if len(up) > 0:
			print "\tup %d" % len(up),
		else:
			print "\t",
		if len(down) > 0:
			print "\tdown %d" % len(down)
		else:
			print
		sumPrec += prec
		sumPrecReranked += precsReranked[qid]
		sumUp += len(up)
		sumDown += len(down)
		
print "-" * 40
print "avg\t%.2f\t%.2f\t%+.2f\tup %d\tdown %d" % (sumPrec/len(QUERY_RANGE), sumPrecReranked/len(QUERY_RANGE), (sumPrecReranked-sumPrec)/len(QUERY_RANGE), sumUp, sumDown)
