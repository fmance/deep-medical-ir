import os
import sys
import scipy.stats

sys.path.insert(0, "../utils/")
import utils


FILE1 = sys.argv[1]
FILE2 = sys.argv[2]

results1 = utils.readResults(FILE1)
results2 = utils.readResults(FILE2)

def rec(x):
	return 1.0/(20.0 + float(x))

out = open(FILE1 + ".rrf", "w")
for qid in sorted(results1.keys()):
	qidRes1 = results1[qid]
	qidRes2 = results2[qid]
	docs1, ranks1, _ = zip(*qidRes1)
	docs2, ranks2, _ = zip(*qidRes2)
	ranks1 = dict(zip(docs1, ranks1))
	ranks2 = dict(zip(docs2, ranks2))
	docScores = {}
	for doc in list(set(docs1) | set(docs2)):
		docScores[doc] = rec(ranks1[doc]) + rec(ranks2[doc])
	docScores = sorted(docScores.items(), key=lambda ds:ds[1], reverse=True)
	rank = 1
	for did, score in docScores[:100]:
		out.write("%d Q0 %s %d %f STANDARD\n" % (qid, did, rank, score))
		rank += 1
out.close()
		
