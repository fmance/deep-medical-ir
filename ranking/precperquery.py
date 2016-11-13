import os
import sys
import subprocess
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import lines
from cycler import cycler
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

sys.path.insert(0, "../utils/")
import utils
from scipy import stats

trecEval = "../eval/trec_eval.9.0/trec_eval"

CLASS_ID = sys.argv[1]
CLASSIFIER = sys.argv[2]
FUSION_STR = " ".join(sys.argv[3:])

if CLASS_ID == "all" or CLASS_ID == "regression":
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
	print "-" * 120
	
	diffPrecs = [rrPrec-bsPrec for (rrPrec, bsPrec) in zip(rerankedPrecs, baselinePrecs)]
	print "Diag\t", np.mean(diffPrecs[:10]), " orig: ", np.mean(baselinePrecs[:10]), ", rel improvement: ", 
	print "%.2f" % (100 * (np.mean(diffPrecs[:10]) / np.mean(baselinePrecs[:10])))
	
	print "Test\t", np.mean(diffPrecs[10:20]), " orig: ", np.mean(baselinePrecs[10:20]), ", rel improvement: ", 
	print "%.2f" % (100 * (np.mean(diffPrecs[10:20]) / np.mean(baselinePrecs[10:20])))
	
	print "Treat\t", np.mean(diffPrecs[20:]), " orig: ", np.mean(baselinePrecs[20:]), ", rel improvement: ", 
	print "%.2f" % (100 * (np.mean(diffPrecs[20:]) / np.mean(baselinePrecs[20:])))
	
	print "=" * 120
	return baselinePrecs, rerankedPrecs, positiveMoves, negativeMoves

def run(target):
	year = target[:4]
	qrelsFile = "../data/qrels/qrels-treceval-" + year + ".txt"
	resultsFile = "../ir/results/results-" + target + ".txt"

	if CLASS_ID == "all":
		rerankedResultsFile = resultsFile + ".reranked." + CLASSIFIER 
	elif CLASS_ID == "regression":
		rerankedResultsFile = os.path.join("supervised", "results-" + target + "-SVMPerf.04.0.001.hedges-test.9.5.reranked.txt")
	else:
		rerankedResultsFile = resultsFile + ".reranked." + CLASS_ID + "." + CLASSIFIER

	return getPrecs(qrelsFile, resultsFile, rerankedResultsFile)

def barPlot(baselinePrecs, rerankedPrecs, title):
	print "Plotting", title
	
	diffPerQuery = np.array([(reranked-base) for reranked,base in zip(rerankedPrecs, baselinePrecs)])
	positiveDiffs = [diff if diff > 0 else 0 for diff in diffPerQuery]
	negativeDiffs = [diff if diff < 0 else 0 for diff in diffPerQuery]
	
	plt.plot(range(0,32,1), [0] * len(range(0,32,1)), color="black", lw=2)
	
	baselineBar = plt.bar(QUERY_RANGE_NP, baselinePrecs, color="#99B6CF", align="center", label="Baseline")
	posDiffBar = plt.bar(QUERY_RANGE_NP, positiveDiffs, color="#2A6FA8", align="center", bottom=baselinePrecs, label="Increase")
	negDiffBar = plt.bar(QUERY_RANGE_NP, negativeDiffs, color="#CCB4B5", align="center", bottom=[0] * len(QUERY_RANGE_NP), label="Decrease")
	
	marker1 = lines.Line2D([], [], marker="s", markersize=25, linewidth=0, color="#2A6FA8", markeredgewidth=0)
	marker2 = lines.Line2D([], [], marker="s", markersize=25, linewidth=0, color="#99B6CF", markeredgewidth=0)
	marker3 = lines.Line2D([], [], marker="s", markersize=25, linewidth=0, color="#CCB4B5", markeredgewidth=0)
							
	plt.title(FUSION_STR + u" \u2014 " + title , loc="left", fontsize="large", fontweight="bold", y=1.19,x=-0.0335)

	ax = plt.gca()
	
	plt.xlabel("Query")
	plt.ylabel("P@10 (%)", rotation=0)
	ax.yaxis.set_label_coords(0.011,1.07)
	
	ax.set_xticks(QUERY_RANGE_NP)
	ax.set_xticklabels(QUERY_RANGE_NP)
	
	ax.spines["top"].set_visible(False)    
	ax.spines["bottom"].set_visible(False)    
	ax.spines["right"].set_visible(False)    
	ax.spines["left"].set_visible(False) 
	
	ax.get_xaxis().tick_bottom()    
	ax.get_yaxis().tick_left() 
	
	ax.legend((marker1, marker2, marker3), ("Increase", "Baseline", "Decrease"), frameon=False, bbox_to_anchor=(0.405, 1))
	
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
	
	titleExt = "change in P@10 per Query (mean change "
	
	ax = plt.subplot(411)
	barPlot(baseSum2014, rrSum2014, "Summaries 2014 " + titleExt + "%+.2f)" % (np.mean(rrSum2014)-np.mean(baseSum2014)))

	ax = plt.subplot(412)
	barPlot(baseDesc2014, rrDesc2014, "Descriptions 2014 " + titleExt + "%+.2f)" % (np.mean(rrDesc2014)-np.mean(baseDesc2014)))
	
	ax = plt.subplot(413)
	barPlot(baseSum2015, rrSum2015, "Summaries 2015 " + titleExt + "%+.2f)" % (np.mean(rrSum2015)-np.mean(baseSum2015)))
	
	ax = plt.subplot(414)
	barPlot(baseDesc2015, rrDesc2015, "Descriptions 2015 " + titleExt + "%+.2f)" % (np.mean(rrDesc2015)-np.mean(baseDesc2015)))

	plt.subplots_adjust(hspace=0.6)
	
	matplotlib.rcParams.update({'font.size': 25})
	fig = matplotlib.pyplot.gcf()
	fig.set_size_inches(30, 35)


	saveDir = "plots/bar/"
	plt.savefig(saveDir + "/" + CLASS_ID + "." + CLASSIFIER + ".png", bbox_inches="tight")
	plt.close()

#plot()

def ttestPrecs(title, baseline, reranked):
	print title
	print "Baseline =", baseline
	print "Reranked =", reranked
	print "-" * 100
	print "Average improvement =", np.mean(np.array(reranked) - np.array(baseline))
	print stats.ttest_rel(baseline, reranked)
	print "=" * 100

def ttest():
	baseSum2014, rrSum2014, _, _ = run("2014-sum")
	baseDesc2014, rrDesc2014, _, _ = run("2014-desc")
	baseSum2015, rrSum2015, _, _ = run("2015-sum")
	baseDesc2015, rrDesc2015, posDesc2015, negDesc2015 = run("2015-desc")
	baseSum2016, rrSum2016, _, _ = run("2016-sum")
	baseDesc2016, rrDesc2016, _, _ = run("2016-desc")
	baseNote2016, rrNote2016, _, _ = run("2016-note")
	
#	ttestPrecs("SUMMARIES 2014", 	baseSum2014, 	rrSum2014)
#	ttestPrecs("DESCRIPTIONS 2014", baseDesc2014, 	rrDesc2014)
#	ttestPrecs("SUMMARIES 2015", 	baseSum2015, 	rrSum2015)
#	ttestPrecs("DESCRIPTIONS 2015", baseDesc2015, 	rrDesc2015)
#	ttestPrecs("SUMMARIES 2016", 	baseSum2016, 	rrSum2016)
#	ttestPrecs("DESCRIPTIONS 2016", baseDesc2016, 	rrDesc2016)
#	ttestPrecs("NOTES 2016", 		baseNote2016, 	rrNote2016)
	
#	print "All 120"
#	print stats.ttest_rel(baseSum2014 + baseDesc2014 + baseSum2015 + baseDesc2015,  rrSum2014 + rrDesc2014 + rrSum2015 + rrDesc2015)
	
ttest()


















