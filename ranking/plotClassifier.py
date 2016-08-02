#!/usr/bin/python

import os
import sys
import subprocess
from optparse import OptionParser
import pprint
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

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
	return map(float, lines)

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

Y_LIMS = {"diag": [0.28, 0.38], "test": [0.26, 0.36], "treat": [0.35, 0.45], "all": [0.28, 0.38]}

def plotPrecs(precs, classId, color="b", setLimits=False):
	WEIGHT_RANGE = np.linspace(0.0, 1.0, 51)
	baseline = [precs[-1]] * len(precs)

	#####################
#	if setLimits:
#		axes = plt.gca()
#		axes.set_ylim(Y_LIMS[classId])
#	plt.plot(WEIGHT_RANGE, baseline, linewidth=3.0, color="black")
#	plt.plot(WEIGHT_RANGE, precs, linewidth=3.0, color=color)
	#####################
	
	#####################
	axes = plt.gca()
	axes.set_ylim([-0.05, 0.1])
	improvements = [prec - baseline[0] for prec in precs]
	plt.plot(WEIGHT_RANGE, [0] * len(precs), linewidth=3.0, color="black")
	plt.plot(WEIGHT_RANGE, improvements, linewidth=3.0, color=color)
	#####################
	
#	plt.axvline(x=0.6, linewidth=2, color="black")
#	plt.axvline(x=0.9, linewidth=2, color="black")
	plt.grid(linewidth=1)
	
def subplot(string):
	ax = plt.subplot(string)
	ax.spines["top"].set_visible(False)    
	ax.spines["bottom"].set_visible(False)    
	ax.spines["right"].set_visible(False)    
	ax.spines["left"].set_visible(False) 
	ax.get_xaxis().tick_bottom()    
	ax.get_yaxis().tick_left() 
	
	ax.set_yticks(np.arange(-0.5,0.1,0.01),minor=True)
	ax.yaxis.grid(True, which="minor")
	
	ax.set_xticks([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0], minor=True)
	ax.xaxis.grid(True, which='minor')
	
#	plt.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off", labelleft="on")  	

def plotSumDescAllYears(classId, sum2014, sum2015, desc2014, desc2015):
	subplot(321)
	plotPrecs(sum2014, classId, color="red")
	plotPrecs(sum2015, classId)
	plt.title(opts.classifier + " " + classId.upper() + " SUM")
	
	subplot(322)
	plotPrecs(desc2014, classId, color="red")
	plotPrecs(desc2015, classId)
	plt.title(opts.classifier + " " + classId.upper() + " DESC")
	
	subplot(323)
	plotPrecs(np.mean([sum2014, desc2014], axis=0), classId, color="red")
	plt.title(opts.classifier + " " + "AVERAGE DESC+SUM 2014")
	
	subplot(324)
	plotPrecs(np.mean([sum2015, desc2015], axis=0), classId)
	plt.title(opts.classifier + " " + "AVERAGE DESC+SUM 2015")
	
	subplot(325)
	plotPrecs(np.mean([sum2014, sum2015, desc2014, desc2015], axis=0), classId, setLimits=True)
	plt.title(opts.classifier + " " + "AVERAGE SUM & DESC 2014 & 2015")

	matplotlib.rcParams.update({'font.size': 20})
	fig = matplotlib.pyplot.gcf()
	fig.set_size_inches(25, 25)

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


	
	
	


