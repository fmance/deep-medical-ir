import os
import sys
import subprocess
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

sys.path.insert(0, "../utils/")
import utils

trecEval = "../eval/trec_eval.9.0/trec_eval"

CLASS_ID = sys.argv[1]
CLASSIFIER = sys.argv[2]

if CLASS_ID == "all":
	QUERY_RANGE = range(1, 31)
else:
	QUERY_OFFSETS = {"diag": 1, "test": 11, "treat": 21}
	QUERY_OFFSET = QUERY_OFFSETS[CLASS_ID]
	QUERY_RANGE = range(QUERY_OFFSET, QUERY_OFFSET + 10)

QUERY_RANGE_NP = np.array(QUERY_RANGE)

def getPrecsPerQuery(qrelFile, precNum, results):
	output = subprocess.Popen([trecEval, "-q", qrelFile, results], stdout=subprocess.PIPE).communicate()[0]
	output = output.split()
	
	precMap = {}
	for i in range(0, len(output)):
		if output[i] == precNum and output[i+1] != "all":
			qid = int(output[i+1])
			prec = float(output[i+2])
			precMap[qid] = 100 * prec
	
	return precMap
	
def getMovement(qrels, res, resReranked, maxRank):
	relTop10 = set([did for (did, rank, score) in res if qrels.get(did) > 0 and rank <= maxRank])
	relRerankedTop10 = set([did for (did, rank, score) in resReranked if qrels.get(did) > 0 and rank <= maxRank])
	up = relRerankedTop10 - relTop10
	down = relTop10 - relRerankedTop10
	
	originalRanksByDoc = {did:rank for (did, rank, _) in res}
	# relevant docs that went up/down the reranked results
	positiveMove = [did for (did, rank, score) in resReranked if qrels.get(did) > 0 and rank <= originalRanksByDoc[did]]
	negativeMove = [did for (did, rank, score) in resReranked if qrels.get(did) > 0 and rank > originalRanksByDoc[did]]
	
	sumRanks = sum([rank for (did, rank, _) in res if qrels.get(did) > 0])
	sumRanksReranked = sum([rank for (did, rank, _) in resReranked if qrels.get(did) > 0])
	
	return up, down, positiveMove, negativeMove, sumRanks, sumRanksReranked

def getPrecs(qrelsFile, resultsFile, rerankedResultsFile):
	precs = getPrecsPerQuery(qrelsFile, "P_10", resultsFile)
	precsReranked = getPrecsPerQuery(qrelsFile, "P_10", rerankedResultsFile)

	sumPrec = 0.0
	sumPrecReranked = 0.0
	sumUp = 0
	sumDown = 0
	positiveMoveSum = 0
	negativeMoveSum = 0
	sumRanksSum = 0
	sumRanksRerankedSum = 0

	qrels = utils.readQrels(qrelsFile)
	results = utils.readResults(resultsFile)
	resultsReranked = utils.readResults(rerankedResultsFile)

	baselinePrecs = []
	rerankedPrecs = []
	positiveMoves = []
	negativeMoves = []

	for qid, prec in precs.items():
		if qid in QUERY_RANGE:
			queryQrels = dict(qrels[qid])
			queryRes = results[qid]
			queryResRer = resultsReranked[qid]
			up, down, positiveMove, negativeMove, sumRanks, sumRanksReranked = getMovement(queryQrels, queryRes, queryResRer, 10)
			print "%2d\t%6.2f\t%6.2f\t" % (qid, prec, precsReranked[qid]),
			if precsReranked[qid] != prec:
				print "%+.2f" % (precsReranked[qid] - prec),
			if len(up) > 0:
				print "\tup %d" % len(up),
			else:
				print "\t",
			if len(down) > 0:
				print "\tdown %d" % len(down),
			else:
				print "\t",
			print "\t\t%d\t%d\t\t%d\t%d\t%+d" % (len(positiveMove), len(negativeMove), sumRanks, sumRanksReranked, sumRanks-sumRanksReranked)
		
			sumPrec += prec
			sumPrecReranked += precsReranked[qid]
			sumUp += len(up)
			sumDown += len(down)
			positiveMoveSum += len(positiveMove)
			negativeMoveSum += len(negativeMove)
			sumRanksSum += sumRanks
			sumRanksRerankedSum += sumRanksReranked
		
			baselinePrecs.append(prec)
			rerankedPrecs.append(precsReranked[qid])
			positiveMoves.append(len(positiveMove))
			negativeMoves.append(len(negativeMove))
		
	print "-" * 120
	print "avg\t%.2f\t%.2f\t%+.2f\tup %d\tdown %d\t\t%d\t%d\t\t%d\t%d\t%+d" % (sumPrec/len(QUERY_RANGE), sumPrecReranked/len(QUERY_RANGE), (sumPrecReranked-sumPrec)/len(QUERY_RANGE), sumUp, sumDown, positiveMoveSum, negativeMoveSum, sumRanksSum, sumRanksRerankedSum, sumRanksSum-sumRanksRerankedSum)
	print "=" * 120
	return baselinePrecs, rerankedPrecs, positiveMoves, negativeMoves

def run(target):
	year = target[:4]
	qrelsFile = "../data/qrels/qrels-treceval-" + year + ".txt"
	resultsFile = "../ir/results/results-" + target + ".txt"

	if CLASS_ID == "all":
		rerankedResultsFile = resultsFile + ".reranked." + CLASSIFIER 
	else:
		rerankedResultsFile = resultsFile + ".reranked." + CLASS_ID + "." + CLASSIFIER

	return getPrecs(qrelsFile, resultsFile, rerankedResultsFile)

def barPlot(baselinePrecs, rerankedPrecs, title):
	print "Plotting", title

	diffPerQuery = np.array([(reranked-base) for reranked,base in zip(rerankedPrecs, baselinePrecs)])
	positiveDiffs = [diff if diff > 0 else 0 for diff in diffPerQuery]
	negativeDiffsAsPositive = [-diff if diff < 0 else 0 for diff in diffPerQuery]
	
	baselineMinusNegatives = [base-neg for (base,neg) in zip(baselinePrecs, negativeDiffsAsPositive)]
	
	width=0.75
	
	plt.plot(range(0,32,1), [0] * len(range(0,32,1)), color="black")
	
	posDiffBar = plt.bar(QUERY_RANGE_NP, positiveDiffs, edgecolor="#2A6FA8", color="#2A6FA8", align="center",
						bottom=baselinePrecs, label="Improvement P@10", linewidth=3, width=width)
	
	negDiffBar = plt.bar(QUERY_RANGE_NP, negativeDiffsAsPositive, edgecolor="#99B6CF", color="#99B6CF", alpha=0.3,
							align="center", bottom=baselineMinusNegatives, label="Worsening P@10", linewidth=3,  width=width)
	
	baseBar = plt.bar(QUERY_RANGE_NP, baselineMinusNegatives, edgecolor="#99B6CF", color="#99B6CF", align="center",
						label="Baseline P@10", linewidth=3, width=width)
							
	plt.title(title, loc="left", fontsize="large")

	ax = plt.gca()
	ax.set_xticks(QUERY_RANGE_NP)
	ax.set_xticklabels(QUERY_RANGE_NP)
	
	ax.spines["top"].set_visible(False)    
	ax.spines["bottom"].set_visible(False)    
	ax.spines["right"].set_visible(False)    
	ax.spines["left"].set_visible(False) 
	
	ax.get_xaxis().tick_bottom()    
	ax.get_yaxis().tick_left() 
	
#	ax.yaxis.set_major_formatter(FormatStrFormatter("%+d"))
	ax.xaxis.grid(False)
	ax.yaxis.grid(linewidth=1.5)
	
	plt.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off", labelleft="on") 
	
	plt.axis("tight")

def plot():
	plt.style.use("ggplot")

	baseSum2014, rrSum2014, _, _ = run("2014-sum")
	baseDesc2014, rrDesc2014, _, _ = run("2014-desc")
	baseSum2015, rrSum2015, _, _ = run("2015-sum")
	baseDesc2015, rrDesc2015, _, _ = run("2015-desc")
	
	titleExt = "P@10 increase/decrease per query (mean increase: "
	
	ax = plt.subplot(411)
	barPlot(baseSum2014, rrSum2014, "Summaries 2014: " + titleExt + "%.2f%%)" % (np.mean(rrSum2014)-np.mean(baseSum2014)))
#	ax.legend(frameon=False, bbox_to_anchor=(0.49, 1))
	
	ax = plt.subplot(412)
	barPlot(baseDesc2014, rrDesc2014, "Descriptions 2014: " + titleExt + "%.2f%%)" % (np.mean(rrDesc2014)-np.mean(baseDesc2014)))
#	ax.legend(frameon=False, bbox_to_anchor=(0.49, 1))
	
	ax = plt.subplot(413)
	barPlot(baseSum2015, rrSum2015, "Summaries 2015: " + titleExt + "%.2f%%)" % (np.mean(rrSum2015)-np.mean(baseSum2015)))
#	ax.legend(frameon=False, bbox_to_anchor=(0.49, 1))
	
	ax = plt.subplot(414)
	barPlot(baseDesc2015, rrDesc2015, "Descriptions 2015: " + titleExt + "%.2f%%)" % (np.mean(rrDesc2015)-np.mean(baseDesc2015)))
#	ax.legend(frameon=False, bbox_to_anchor=(0.4, 1))
	

	plt.subplots_adjust(hspace=0.3)
	
	matplotlib.rcParams.update({'font.size': 25})
	fig = matplotlib.pyplot.gcf()
	fig.set_size_inches(30, 35)


	saveDir = "plots/bar/"
	plt.savefig(saveDir + "/" + CLASS_ID + "." + CLASSIFIER + ".png", bbox_inches="tight")
	plt.close()

plot()


















