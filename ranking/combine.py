import os
import sys
from collections import defaultdict

sys.path.insert(0, "../utils/")
import utils

CLASS_ID = sys.argv[1]
YEAR = sys.argv[2]

CLASSIFIERS = [
	"LinearSVC.squared_hinge.l2", 
	"SGDClassifier.hinge.l2",
	"SGDClassifier.hinge.elasticnet",
	"SGDClassifier.squared_loss.l2",
	"SGDClassifier.squared_loss.elasticnet",
	"SGDClassifier.epsilon_insensitive.l2",
	"SGDClassifier.epsilon_insensitive.elasticnet",
	"Pipeline.epsilon_insensitive.l2"
]

def getResultsFiles():
	resultsFiles = []
	for classifier in CLASSIFIERS:
		resultsFiles.append("../ir/results/results-" + YEAR + ".txt.reranked." + CLASS_ID + "." + classifier)
	return resultsFiles

def readMultipleResults(resultsFiles):
	resultsList = []
	for resultsFile in resultsFiles:
		results = utils.readResults(resultsFile)
		resultsList.append(results)
	return resultsList
	
def combSum(resultsList):
	combSumResults = {}
	qids = resultsList[0].keys()
	for qid in qids:
		queryResultsList = [results[qid] for results in resultsList]
		resultsSum = defaultdict(float)
		for didRankScores in queryResultsList:
			for did, _, score in didRankScores:
				resultsSum[did] += score # normalize!!!
		combSumResults[qid] = resultsSum
	return combSumResults
	
def writeResults(results, outFile):
	out = open(outFile, "w")
	for qid, queryResults in results.items():
		rank = 1
		queryResults = queryResults.items()
		queryResults.sort(key = lambda docScore : docScore[1], reverse = True)
		for did, score in queryResults:
			out.write("%d Q0 %s %d %f STANDARD\n" % (qid, did, rank, score))
			rank += 1
	out.close()

def run():	
	resultsFiles = getResultsFiles()
	resultsList = readMultipleResults(resultsFiles)
	combinedResults = combSum(resultsList)
	rerankedResultsFile = "../ir/results/results-" + YEAR + ".txt.reranked." + CLASS_ID + ".combined"
	writeResults(combinedResults, rerankedResultsFile)

run()


