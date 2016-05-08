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
		unjudged[qid] = float(len(resIds - qrelIds))/len(resIds)
		print "%d -> %f" % (qid, unjudged[qid])
	print "--------------------"
	return sum(unjudged.values())/len(unjudged.values())

print unjudged(sys.argv[1], sys.argv[2])
