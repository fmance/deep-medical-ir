#!/usr/bin/python

import os
import sys
import subprocess
from optparse import OptionParser
import pprint
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import pickle


op = OptionParser()
op.add_option("--classifier",
			  action="store", default="SGDClassifier.squared_loss.l2",
			  help="classifier.")
op.add_option("--fusion",
			  action="store", default="interpolation",
			  help="fusion method.")
op.add_option("--exp",
			  action="store_true", help="use expanded.")

(opts, args) = op.parse_args()

print "Classifier : " + opts.classifier + ", fusion : " + opts.fusion

if opts.exp:
	EXP = "exp-"
else:
	EXP = ""
	
if opts.fusion == "interpolation":
	FUSION_STR = "LIN. COMB."
else:
	FUSION_STR = opts.fusion.upper()

WEIGHT_RANGE = np.linspace(0.0, 1.0, 51)
	
COLOR_LIST = ['#BD2828', '#1459A8', '#35871E']


def getPrecs(target, withBasic=True):
	classifier = opts.classifier
	if classifier == "best":
		if "diag" in target:
			classifier = "PassiveAggressiveClassifier.hinge"
		if "test" in target:
			classifier = "SGDClassifier.squared_loss.l2"
		if "treat" in target:
			classifier = "SVMPerf.hedges"
	
	rerankCommand = "python simplererank.py " + target + " --classifier " + classifier + " --fusion " + opts.fusion
	if not withBasic:
		rerankCommand += " --no_basic"
	p = subprocess.Popen([rerankCommand], stdout=subprocess.PIPE, shell=True)
	out, _ = p.communicate()
	lines = out.splitlines()
	lines.pop()
	precs = map(float, lines)
	return map(lambda p: p * 100.0, precs)

def getDiff(precs):
	baseline = precs[-1]
	return [prec - baseline for prec in precs]

def getRerankedPrecs(withBasic=True):
	print "Reranking diag"
	DIAG_2014_SUM = getPrecs("diag 2014-" + EXP + "sum", withBasic)
	DIAG_2015_SUM = getPrecs("diag 2015-" + EXP + "sum", withBasic)
	DIAG_2014_DESC = getPrecs("diag 2014-" + EXP + "desc", withBasic)
	DIAG_2015_DESC = getPrecs("diag 2015-" + EXP + "desc", withBasic)

	print "Reranking test"
	TEST_2014_SUM = getPrecs("test 2014-" + EXP + "sum", withBasic)
	TEST_2015_SUM = getPrecs("test 2015-" + EXP + "sum", withBasic)
	TEST_2014_DESC = getPrecs("test 2014-" + EXP + "desc", withBasic)
	TEST_2015_DESC = getPrecs("test 2015-" + EXP + "desc", withBasic)

	print "Reranking treat"
	TREAT_2014_SUM = getPrecs("treat 2014-" + EXP + "sum", withBasic)
	TREAT_2015_SUM = getPrecs("treat 2015-" + EXP + "sum", withBasic)
	TREAT_2014_DESC = getPrecs("treat 2014-" + EXP + "desc", withBasic)
	TREAT_2015_DESC = getPrecs("treat 2015-" + EXP + "desc", withBasic)

	print "Computing means"
	ALL_2014_SUM = np.mean([DIAG_2014_SUM, TEST_2014_SUM, TREAT_2014_SUM], axis=0)
	ALL_2015_SUM = np.mean([DIAG_2015_SUM, TEST_2015_SUM, TREAT_2015_SUM], axis=0)
	ALL_2014_DESC = np.mean([DIAG_2014_DESC, TEST_2014_DESC, TREAT_2014_DESC], axis=0)
	ALL_2015_DESC = np.mean([DIAG_2015_DESC, TEST_2015_DESC, TREAT_2015_DESC], axis=0)

	PRECS = {"diag": 	[DIAG_2014_SUM, DIAG_2015_SUM, DIAG_2014_DESC, DIAG_2015_DESC], \
			 "test": 	[TEST_2014_SUM, TEST_2015_SUM, TEST_2014_DESC, TEST_2015_DESC], \
			 "treat": 	[TREAT_2014_SUM, TREAT_2015_SUM, TREAT_2014_DESC, TREAT_2015_DESC] }
			 
	return ALL_2014_SUM, ALL_2015_SUM, ALL_2014_DESC, ALL_2015_DESC, PRECS

def plotDiffs(diffs, labels, title, texts):
	axes = plt.gca()
	axes.set_ylim([-4, 12])
	
	plt.xlabel("BM25 Weight")
	plt.ylabel("Precision@10", rotation=0)
	axes.yaxis.set_label_coords(0.065,1.04)

	baseline, = plt.plot(WEIGHT_RANGE, [0] * len(diffs[0]), linewidth=3.0, color="black", label="Baseline", zorder=10)
	
	lines = []
	for diff, label in zip(diffs, labels):
		line, = plt.plot(WEIGHT_RANGE, diff, linewidth=3.0, label=label, zorder=10) #, marker="D", markersize=6, markeredgewidth=0)
		lines.append(line)
	
	for y in range(-4, 12, 2):
		plt.plot(np.linspace(0, 1, 11), [y] * len(np.linspace(0,1,11)),  color="white", lw=1)
	
#	axes.legend(handles=lines, loc="upper left", frameon=False)

	for text, color in zip(texts, COLOR_LIST):
		plt.text(text[0], text[1], text[2], fontsize="large", color=color)
	
#	axes.set_axis_bgcolor("0.92")
#	axes.grid(color="white", linestyle="-", linewidth=1)
	
#	axes.grid()
#	axes.set_axisbelow(True)
	
	axes.get_xaxis().grid(False)
	
	plt.title(title, loc="left", y=1.11,x=-0.05, fontweight="bold")

def pickleDiffBasicNoBasic(withBasicList, noBasicList):
	meanOvrWithBasic = np.mean(withBasicList, axis=0)
	meanOvrNoBasic = np.mean(noBasicList, axis=0)
	
	diffMeanWithBasic = getDiff(meanOvrWithBasic)
	diffMeanNoBasic = getDiff(meanOvrNoBasic)
	
 	pickle.dump((diffMeanWithBasic, diffMeanNoBasic), open("basic-vs-non-basic." + opts.fusion + ".pickle", "w"))

def plotBasicVsNonBasic(diffBasic, diffNoBasic, textPos, title):
	ax = plt.gca()
	ax.set_ylim([-4, 8])
	plt.xlabel("BM25 Weight")
	plt.ylabel("Precision@10", rotation=0)
	ax.yaxis.set_label_coords(0.065,1.02)
	
	plt.plot(WEIGHT_RANGE, diffBasic, linewidth=3.0, zorder=10)
	plt.plot(WEIGHT_RANGE, diffNoBasic, linewidth=3.0, zorder=10)
	
	for y in range(-4, 8, 2):
		plt.plot(np.linspace(0, 1, 11), [y] * len(np.linspace(0,1,11)),  color="white", lw=1.5)
	
	plt.fill_between(WEIGHT_RANGE, diffBasic, diffNoBasic, color="#BD2828", where=(np.array(diffBasic)>=np.array(diffNoBasic)), zorder=10, alpha=0.1)
	
	plt.text(textPos[0][0], textPos[0][1], "With Keyword Counter", fontsize="large", color='#BD2828')
	plt.text(textPos[1][0], textPos[1][1], "Without Keyword Counter", fontsize="large", color='#1459A8')
	plt.title(title, loc="left", y=1.09,x=-0.05, fontweight="bold")
	
	ax.get_xaxis().grid(False)
	ax.get_yaxis().grid(False)

def readAndPlotBasicVsNonBasic():
	diffBasicInterp, diffNoBasicInterp = pickle.load(file("basic-vs-non-basic.interpolation.pickle"))
	diffBasicRRF, diffNoBasicRRF = pickle.load(file("basic-vs-non-basic.rrf.pickle"))
	diffBasicBorda, diffNoBasicBorda = pickle.load(file("basic-vs-non-basic.borda.pickle"))
	
	plt.style.use("ggplot")
	
	plt.plot(WEIGHT_RANGE, [0] * len(diffBasicInterp), linewidth=3.0, color="black", label="Baseline", zorder=10)

	TEXT_POSITIONS_DICT = {"interpolation": [(0.06, 3), (0.405, -1)],
					  "rrf":  [(0.00, 3), (0.33, 0)],
					  "borda": [(0, 3.74), (0.32, 1.5)]
					}

	titlePrefix = "Keyword Counter Contribution"
	
	subplot(131)
	plotBasicVsNonBasic(diffBasicInterp, diffNoBasicInterp, TEXT_POSITIONS_DICT["interpolation"], titlePrefix + " (Lin. Comb.)")
	
	subplot(132)
	plotBasicVsNonBasic(diffBasicRRF, diffNoBasicRRF, TEXT_POSITIONS_DICT["rrf"], titlePrefix + " (RRF)")
	
	subplot(133)
	plotBasicVsNonBasic(diffBasicBorda, diffNoBasicBorda, TEXT_POSITIONS_DICT["borda"], titlePrefix + " (Borda)")
	
	postConfig()
	
	plt.savefig("plots/basic-vs-non-basic.png", bbox_inches="tight")
	plt.close()
	
def configPlot(ax):
	ax.spines["top"].set_visible(False)    
	ax.spines["bottom"].set_visible(False)    
	ax.spines["right"].set_visible(False)    
	ax.spines["left"].set_visible(False) 
	
	ax.get_xaxis().tick_bottom()    
	ax.get_yaxis().tick_left() 
	
	ax.yaxis.set_major_formatter(FormatStrFormatter("%+d"))
	
	plt.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off", labelleft="on")  	

def postConfig():
	plt.subplots_adjust(wspace=0.08)

	matplotlib.rcParams.update({'font.size': 20,
								'xtick.labelsize':'x-large',
								'ytick.labelsize':'x-large'})
	
	fig = matplotlib.pyplot.gcf()
	fig.set_size_inches(40, 8)

def subplot(string):
	plt.rc('axes', prop_cycle=(cycler('color', ['#BD2828', '#1459A8', '#35871E'])))
	ax = plt.subplot(string)
	configPlot(ax)

def plotSumDescAllYears(classId, sum2014, sum2015, desc2014, desc2015):
	diffSum2014 = getDiff(sum2014)
	diffSum2015 = getDiff(sum2015)
	diffDesc2014 = getDiff(desc2014)
	diffDesc2015 = getDiff(desc2015)
	
	meanSum = np.mean([sum2014, sum2015], axis=0)
	meanDesc = np.mean([desc2014, desc2015], axis=0)
	
	diffMeanSum = getDiff(meanSum)
	diffMeanDesc = getDiff(meanDesc)
		
	mean2014 = np.mean([sum2014, desc2014], axis=0)
	mean2015 = np.mean([sum2015, desc2015], axis=0)
	meanOvr = np.mean([sum2014, sum2015, desc2014, desc2015], axis=0)
	
	diffMean2014 = getDiff(mean2014)
	diffMean2015 = getDiff(mean2015)
	diffMeanOvr = getDiff(meanOvr)

	plt.style.use("ggplot")

	subplot(131)
	
	if opts.fusion == "interpolation":
		if opts.classifier == "SVMPerf.04.0.001.hedges":
			sumTexts = [(0.05, 5.78, "Summaries 2014"), (0.34, 2.5, "Summaries 2015")]
			descTexts = [(0.2, 7.5, "Descriptions 2014"), (0.37, 2.9, "Descriptions 2015")]
			meanTexts = [(0.25, 7.7, "Mean 2014"), (0.64, 1.5, "Mean 2015"), (0.29, 4.2, "Mean 2014 & 2015")]
		elif opts.classifier == "SVMPerf.05.0.001.hedges":
			sumTexts = [(0.03, 5.78, "Summaries 2014"), (0.36, 2.5, "Summaries 2015")]
			descTexts = [(0.2, 7.4, "Descriptions 2014"), (0.38, 2.7, "Descriptions 2015")]
			meanTexts = [(0.26, 7.7, "Mean 2014"), (0.66, 0.88, "Mean 2015"), (0.29, 4.2, "Mean 2014 & 2015")]
	elif opts.fusion == "rrf":
		if opts.classifier == "SGDClassifier.squared_loss.elasticnet.hedges":
			sumTexts = [(0.04, 7.3, "Summaries 2014"), (0.3, 2.5, "Summaries 2015")]
			descTexts = [(0.01, 7.5, "Descriptions 2014"), (0.37, 3.2, "Descriptions 2015")]
			meanTexts = [(0.14, 7.7, "Mean 2014"), (0.59, 1.0, "Mean 2015"), (0.27, 4.5, "Mean 2014 & 2015")]
	else:
		if opts.classifier == "SGDClassifier.squared_loss.elasticnet.hedges":
			sumTexts = [(0.04, 7.1, "Summaries 2014"), (0.26, 2.3, "Summaries 2015")]
			descTexts = [(0.25, 6.3, "Descriptions 2014"), (0.37, 2.3, "Descriptions 2015")]
			meanTexts = [(0.09, 7.7, "Mean 2014"), (0.59, 0.6, "Mean 2015"), (0.27, 4.4, "Mean 2014 & 2015")]
	
	plotDiffs([diffSum2014, diffSum2015],
				["Summaries 2014", "Summaries 2015"],
				"Summaries Precision@10 improvements",
				sumTexts
				)
	
	subplot(132)
	plotDiffs([diffDesc2014, diffDesc2015],
				["Descriptions 2014", "Descriptions 2015"],
				"Descriptions Precision@10 improvements",
				descTexts
				)
	
	subplot(133)
	plotDiffs([diffMean2014, diffMean2015, diffMeanOvr],
				["Mean 2014", "Mean 2015", "Mean 2014 & 2015"],
				"Mean Precision@10 improvements",
				meanTexts
				)

	postConfig()

	saveDir = "plots/" + opts.fusion + "/" + classId
	if not os.path.exists(saveDir):
		print "Creating " + saveDir 
		os.makedirs(saveDir)

	print "Plotting " + classId + " to " + saveDir
	plt.savefig(saveDir + "/" + classId + "." + opts.classifier + EXP + ".png", bbox_inches="tight")
	plt.close()



def plotClass(classId, precsDict):
	plotSumDescAllYears(classId, *precsDict[classId])

def plotAllClasses(all2014Sum, all2015Sum, all2014Desc, all2015Desc):
	plotSumDescAllYears("all", all2014Sum, all2015Sum, all2014Desc, all2015Desc)

all2014Sum, all2015Sum, all2014Desc, all2015Desc, precsDict = getRerankedPrecs(withBasic=True)

plotAllClasses(all2014Sum, all2015Sum, all2014Desc, all2015Desc)
plotClass("diag", precsDict)
plotClass("test", precsDict)
plotClass("treat", precsDict)

##all2014SumNoBasic, all2015SumNoBasic, all2014DescNoBasic, all2015DescNoBasic, precsDictNoBasic = getRerankedPrecs(withBasic=False)
##pickleDiffBasicNoBasic([all2014Sum, all2015Sum, all2014Desc, all2015Desc],
##					[all2014SumNoBasic, all2015SumNoBasic, all2014DescNoBasic, all2015DescNoBasic])

#readAndPlotBasicVsNonBasic()

	
	
	


