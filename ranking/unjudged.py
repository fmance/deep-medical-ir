import sys

sys.path.insert(0, "../utils/")
import utils

def unjudged(qrelsFile, resultsFile):
	qrels = utils.readQrels(qrelsFile)
	results = utils.readResults(resultsFile)
	unjudged = {}
	for qid in results.keys():
		qrelIds = set([did for (did, _) in qrels[qid]])
		resIds = set([did for (did, _, _) in results[qid][:10]])
		unjudged[qid] = len(resIds - qrelIds)
		print "%d -> %d" % (qid, unjudged[qid])
	print "--------------------"
	totalUnjudged = sum(unjudged.values())
	return float(totalUnjudged)/(len(results.keys()) * 10)

print "unjudged=%.2f" % unjudged(sys.argv[1], sys.argv[2])
