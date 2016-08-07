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

if opts.exp:
	EXP = "exp-"
else:
	EXP = ""

def getPrecs(target):
	classifier = opts.classifier
	if classifier == "best":
		if "diag" in target:
			classifier = "PassiveAggressiveClassifier.hinge"
		if "test" in target:
			classifier = "SGDClassifier.squared_loss.l2"
		if "treat" in target:
			classifier = "SVMPerf.hedges"
	p = subprocess.Popen(["python simplererank.py " + target + " --classifier " + classifier + " --fusion " + opts.fusion],
							stdout=subprocess.PIPE, shell=True)
	out, _ = p.communicate()
	lines = out.splitlines()
	lines.pop()
	precs = map(float, lines)
	return map(lambda p: p * 100.0, precs)

print "Classifier : " + opts.classifier + ", fusion : " + opts.fusion

print "Reranking diag"
DIAG_2014_SUM = getPrecs("diag 2014-" + EXP + "sum")
DIAG_2015_SUM = getPrecs("diag 2015-" + EXP + "sum")
DIAG_2014_DESC = getPrecs("diag 2014-" + EXP + "desc")
DIAG_2015_DESC = getPrecs("diag 2015-" + EXP + "desc")

print "Reranking test"
TEST_2014_SUM = getPrecs("test 2014-" + EXP + "sum")
TEST_2015_SUM = getPrecs("test 2015-" + EXP + "sum")
TEST_2014_DESC = getPrecs("test 2014-" + EXP + "desc")
TEST_2015_DESC = getPrecs("test 2015-" + EXP + "desc")

print "Reranking treat"
TREAT_2014_SUM = getPrecs("treat 2014-" + EXP + "sum")
TREAT_2015_SUM = getPrecs("treat 2015-" + EXP + "sum")
TREAT_2014_DESC = getPrecs("treat 2014-" + EXP + "desc")
TREAT_2015_DESC = getPrecs("treat 2015-" + EXP + "desc")

print "Computing means"
ALL_2014_SUM = np.mean([DIAG_2014_SUM, TEST_2014_SUM, TREAT_2014_SUM], axis=0)
ALL_2015_SUM = np.mean([DIAG_2015_SUM, TEST_2015_SUM, TREAT_2015_SUM], axis=0)
ALL_2014_DESC = np.mean([DIAG_2014_DESC, TEST_2014_DESC, TREAT_2014_DESC], axis=0)
ALL_2015_DESC = np.mean([DIAG_2015_DESC, TEST_2015_DESC, TREAT_2015_DESC], axis=0)

PRECS = {"diag": 	[DIAG_2014_SUM, DIAG_2015_SUM, DIAG_2014_DESC, DIAG_2015_DESC], \
		 "test": 	[TEST_2014_SUM, TEST_2015_SUM, TEST_2014_DESC, TEST_2015_DESC], \
		 "treat": 	[TREAT_2014_SUM, TREAT_2015_SUM, TREAT_2014_DESC, TREAT_2015_DESC] }

#def getPrecsAllClasses(targetWithoutClass):
#	diag = getPrecs("diag " + targetWithoutClass)
#	test = getPrecs("test " + targetWithoutClass)
#	treat = getPrecs("treat " + targetWithoutClass)
#	return np.mean([diag, test, treat], axis=0)

WEIGHT_RANGE = np.linspace(0.0, 1.0, 51)

def plotDiffs(diffs, labels, title, texts):
	axes = plt.gca()
	axes.set_ylim([-5, 10])
	
	plt.xlabel("BM25 Weight")

	baseline, = plt.plot(WEIGHT_RANGE, [0] * len(diffs[0]), linewidth=3.0, color="black", label="Baseline", zorder=10)
	
	lines = []
	for diff, label in zip(diffs, labels):
		line, = plt.plot(WEIGHT_RANGE, diff, linewidth=3.0, label=label, zorder=10)
		lines.append(line)
	
	for y in range(-4, 10, 1):
		plt.plot(np.linspace(0, 1, 11), [y] * len(np.linspace(0,1,11)),  color="white", lw=1)
	
#	axes.legend(handles=lines, loc="upper left", frameon=False)

	for text in texts:
		plt.text(text[0], text[1], text[2], fontsize="large")
	
#	axes.set_axis_bgcolor("0.92")
#	axes.grid(color="white", linestyle="-", linewidth=1)
	
#	axes.grid()
#	axes.set_axisbelow(True)
	
	axes.get_xaxis().grid(False)
	
	plt.title(title)

def getDiff(precs):
	baseline = precs[-1]
	return [prec - baseline for prec in precs]

def subplot(string):
	plt.rc('axes', prop_cycle=(cycler('color', ['#BD2828', '#1459A8', '#35871E'])))

	ax = plt.subplot(string)
	
	ax.spines["top"].set_visible(False)    
	ax.spines["bottom"].set_visible(False)    
	ax.spines["right"].set_visible(False)    
	ax.spines["left"].set_visible(False) 
	
	ax.get_xaxis().tick_bottom()    
	ax.get_yaxis().tick_left() 
	
#	ax.set_yticks(range(-5,11,1),minor=True)
#	ax.yaxis.grid(True, which="minor")
#	
#	ax.set_xticks([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0], minor=True)
#	ax.xaxis.grid(True, which='minor')

	ax.yaxis.set_major_formatter(FormatStrFormatter("%+d"))
	
	plt.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off", labelleft="on")  	

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
	plotDiffs([diffSum2014, diffSum2015],
				["Summaries 2014", "Summaries 2015"],
				"Summaries P@10 improvements",
				[(0.05, 5.78, "Summaries 2014"), (0.34, 2.5, "Summaries 2015")]
				)
	
	subplot(132)
	plotDiffs([diffDesc2014, diffDesc2015],
				["Descriptions 2014", "Descriptions 2015"],
				"Descriptions P@10 improvements",
				[(0.2, 7.5, "Descriptions 2014"), (0.37, 2.9, "Descriptions 2015")]
				)
	
	subplot(133)
	plotDiffs([diffMean2014, diffMean2015, diffMeanOvr],
				["Mean 2014", "Mean 2015", "Mean 2014 & 2015"],
				"Mean P@10 improvements",
				[(0.25, 7.7, "Mean 2014"), (0.64, 1.5, "Mean 2015"), (0.29, 4.2, "Mean 2014 & 2015")]
				)

	plt.subplots_adjust(wspace=0.08)

	matplotlib.rcParams.update({'font.size': 20})
	fig = matplotlib.pyplot.gcf()
	fig.set_size_inches(40, 8)

	saveDir = "plots/" + opts.fusion + "/" + classId
	if not os.path.exists(saveDir):
		print "Creating " + saveDir 
		os.makedirs(saveDir)

	print "Plotting " + classId + " to " + saveDir
	plt.savefig(saveDir + "/" + classId + "." + opts.classifier + EXP + ".png", bbox_inches="tight")
	plt.close()

def plotClass(classId):
	plotSumDescAllYears(classId, *PRECS[classId])

def plotAllClasses():
	plotSumDescAllYears("all", ALL_2014_SUM, ALL_2015_SUM, ALL_2014_DESC, ALL_2015_DESC)

plotAllClasses()
plotClass("diag")
plotClass("test")
plotClass("treat")


	
	
	


