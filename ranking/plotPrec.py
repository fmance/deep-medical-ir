import os
import sys
from collections import defaultdict
import numpy as np
from optparse import OptionParser

import rankutils

# parse commandline arguments
op = OptionParser()
op.add_option("--year",
			  action="store", default="all",
			  help="year - 2014/2015/all(default)")
op.add_option("--cat",
			  action="store", default="all",
			  help="category - diag/test/treat/all(default)")
op.add_option("--surface", action="store_true", default=False)
op.add_option("--title_prefix", default="")

(opts, args) = op.parse_args()

YEAR_MAP = {}
if opts.year == "all":
	YEAR_MAP["2014"] = "2014"
	YEAR_MAP["2015"] = "2015"
	TITLE_YEARS = "2014 + 2015"
else:
	YEAR_MAP["2014"] = opts.year
	YEAR_MAP["2015"] = opts.year
	TITLE_YEARS = opts.year

if opts.cat == "all":
	SCORE_FILES_2014 = [classId + "-" + YEAR_MAP["2014"] + ".txt" for classId in ["diag", "test", "treat"]]
	SCORE_FILES_2015 = [classId + "-" + YEAR_MAP["2015"] + ".txt" for classId in ["diag", "test", "treat"]]
	TITLE_CATS = "DIAG, TEST, TREAT"
else:
	SCORE_FILES_2014 = [opts.cat + "-" + YEAR_MAP["2014"] + ".txt"]
	SCORE_FILES_2015 = [opts.cat + "-" + YEAR_MAP["2015"] + ".txt"]
	TITLE_CATS = opts.cat.upper()

TITLE = opts.title_prefix + TITLE_CATS + " - " + TITLE_YEARS

	
def readScores(infile):
	scores = {}
	for line in open(infile):
		parts = line.split()
		bm25Weight = float(parts[0])
		classifierWeight = float(parts[1])
		p10 = float(parts[2])
#		if classifierWeight != 1.0:
#			continue
		scores[(bm25Weight, classifierWeight)] = p10
	return scores

def maxAvgScores(scoreFiles2014, scoreFiles2015):
	scores2014 = [readScores(scoreFile) for scoreFile in scoreFiles2014]
	scores2015 = [readScores(scoreFile) for scoreFile in scoreFiles2015]
	
	maxAvg = 0.0
	max2014 = 0.0
	max2015 = 0.0
	allP10s = []
	for weightKey in scores2014[0].keys():
		p2014 = np.mean([scores[weightKey] for scores in scores2014])
		p2015 = np.mean([scores[weightKey] for scores in scores2015])
		avg = (p2014+p2015)/2.0
		allP10s.append((weightKey[0], weightKey[1], avg))
		if avg > maxAvg:
			maxAvg = avg
			max2014 = p2014
			max2015 = p2015
		if weightKey == (1.0, 1.0):
			baseline2014 = p2014
			baseline2015 = p2015
	
	allP10s = sorted(allP10s, key=lambda (bw, cw, _): (bw, cw))		
	maxKeys = [(bw, cw) for bw, cw, score in allP10s if score == maxAvg]
	baseline = allP10s[-1][2]
	
	print "Baseline=%.2f -> MaxP10=%.2f (%.2f->%.2f (%+.2f) / %.2f->%.2f (%+.2f))" %\
			tuple(map(lambda x: x*100, [baseline, maxAvg, baseline2014, max2014, max2014-baseline2014, baseline2015, max2015, max2015 - baseline2015]))
	rankutils.printBestWeights(maxKeys)
	if opts.surface:
		rankutils.plotAllp10s3d(allP10s)
	else:
		rankutils.plotAllp10sContour(allP10s, TITLE)
	
maxAvgScores(SCORE_FILES_2014, SCORE_FILES_2015)	
	
