#!/bin/python

import sys
import os
import random
import codecs
import gensim

sys.path.insert(0, "../utils/")
import utils

MIN_DOC_LEN = 1000
MAX_DOC_LEN = 5000
MAX_NN_DOC_LEN = 500
EMBED_SIZE = 100

CATEGORY = sys.argv[1]

CLASSIFICATION_DATA_DIR = "data/"
ANALYZED_DIR = os.path.join(utils.DATA_DIR, "analyzed/analyzed-2014+2015") #os.path.join(CLASSIFICATION_DATA_DIR, "sentences")
ANALYZED_2016_DIR = os.path.join(utils.DATA_DIR, "analyzed/analyzed-2016")

qrels2014 = utils.readQrels2014()
qrels2015 = utils.readQrels2015()
qrels2016 = utils.readQrels2016()
qrelsDocIds = set(utils.getQrelsDocIds(qrels2014)) | set(utils.getQrelsDocIds(qrels2015)) | set(utils.getQrelsDocIds(qrels2016))

results2014AllModels = utils.readResultsAllModels(2014)
results2015AllModels = utils.readResultsAllModels(2015)
results2016AllModels = utils.readResultsAllModels(2016)
resultsDocIds = map(utils.getResultsDocIds, results2014AllModels) + map(utils.getResultsDocIds, results2015AllModels) \
					+ map(utils.getResultsDocIds, results2016AllModels)

#results2016AllModels = utils.readResultsAllModels(2016)
#resultsDocIds = map(utils.getResultsDocIds, results2016AllModels) 

resultsDocIds = set.union(*map(set, resultsDocIds))

def readPmcIds(pmcIdsFile):
	return set(map(lambda pmcid: int(pmcid[3:]), open(pmcIdsFile).read().split()))


def getPositivePmcIds(category):
	catDir = os.path.join(CLASSIFICATION_DATA_DIR, category, "positive-ids")
	posIds = readPmcIds(os.path.join(catDir, "positive-pmc-ids.txt"))

#	if category == "diag":
#		posIds |= readPmcIds(os.path.join(catDir, "diag-services.txt"))
#
#	if category == "test":
#		posIds |= readPmcIds(os.path.join(catDir, "caries-tests.txt"))
#		posIds |= readPmcIds(os.path.join(catDir, "diag-test-and-procedures.txt"))
#		posIds |= readPmcIds(os.path.join(catDir, "psycho-tests.txt"))
#		posIds |= readPmcIds(os.path.join(catDir, "tox-tests.txt"))
#	if category == "treat":
#		posIds |= readPmcIds(os.path.join(catDir, "treatment-outcome.txt"))
#		posIds |= readPmcIds(os.path.join(catDir, "therapy.txt"))
#		posIds |= readPmcIds(os.path.join(catDir, "therapeutic-use.txt"))

	return posIds

def getPositiveRelaxedPmcIds(category):
	catDir = os.path.join(CLASSIFICATION_DATA_DIR, category, "positive-ids")
	
	# for diag: open access[filter] AND diagnosis[MeSH major topic]
	# for treat: open access[filter] AND therapeutics[MeSH]
	# for test: Physical Examination[mh]
	return readPmcIds(os.path.join(catDir, "positive-pmc-ids-relaxed-more.txt"))

def getNegativePmcIds(category):
	catDir = os.path.join(CLASSIFICATION_DATA_DIR, category, "positive-ids")
	return readPmcIds(os.path.join(catDir, "negative-pmc-ids.txt"))

def getTrainingAndTestIdsForCategory(category):
	positiveDocIds = getPositivePmcIds(category) & utils.VALID_DOC_IDS # nonQrelsOrResultsDids
	negativeDocIds = utils.VALID_DOC_IDS - getPositiveRelaxedPmcIds(category)   #nonQrelsOrResultsDids - getPositiveRelaxedPmcIds(category)
	print "Negative pmc ids before removing mesh-tagged", len(negativeDocIds)
	negativeDocIds &= set(utils.readInts(os.path.join(CLASSIFICATION_DATA_DIR, "mesh-tagged-pmcids.txt")))
	positiveDocIds = list(positiveDocIds)
	negativeDocIds = list(negativeDocIds)
	print "Total pos %d, total neg %d" % (len(positiveDocIds), len(negativeDocIds))
	random.shuffle(positiveDocIds)
	random.shuffle(negativeDocIds)
	numIds = min(len(positiveDocIds), len(negativeDocIds))
	positiveDocIds = positiveDocIds[:numIds]
	negativeDocIds = negativeDocIds[:numIds]
	return positiveDocIds, negativeDocIds

def splitTrainTest(ids):
	trainSize = int(len(ids) * 0.8)
	return ids[:trainSize], ids[trainSize:]

def getWords(filename):
	return codecs.open(filename, "r", "utf-8").read().split()

def getTitleWords(filename):
	return codecs.open(filename, "r", "utf-8").read().splitlines()[0].split()

def readVocabMap():
	print "Reading vocabulary map"
	vocabMap = {}
	for line in codecs.open("nn/vocmap.txt", "r", "utf-8"):
		parts = line.split()
		vocabMap[parts[0]] = int(parts[1])
	return vocabMap

# !! also account for <PAD>
# the w2v floats are truncated to 6 digits
def writeEmbeddings():
    print "Reading word2vec model"
    model = gensim.models.Word2Vec.load("nn/word2vec/model")
    inverseMap = {index: word for word, index in VOCAB_MAP.items()}
    out = open("nn/embeddings.txt", "w")

    out.write("%s\n" % ("0.0 " * EMBED_SIZE)) # zeros for <PAD/> (index 0)
    for index in range(1, 1 + len(inverseMap)):
    	word = inverseMap[index]
    	embedding = " ".join(str(x) for x in model[word])
        out.write("%s\n" % embedding)
        if (index % 10000 == 0):
            print "Wrote up to word %d" % index

    out.close()

def writeIrResultsIds():
	out = open("data/hedges/results-pmcids.txt", "w")
	for did in resultsDocIds:
		out.write("%d\n" % did)
	out.close()

def writeDocsData(docIds, labels, wordsFile, mappingsFile, labelsFile, nnLabelsFile, idsFile, ignoreShortDocs=False):
	wordsOut = codecs.open(wordsFile, "w", "utf-8")
	mappingsOut = codecs.open(mappingsFile, "w", "utf-8")
	labelsOut = open(labelsFile, "w")
	nnLabelsOut = open(nnLabelsFile, "w")
	idsOut = open(idsFile, "w")

	fnames = map(lambda did: str(did) + ".txt", docIds)
	pathsDict = utils.getFilePaths(fnames, ANALYZED_DIR)
	pathsDict2016 = utils.getFilePaths(fnames, ANALYZED_2016_DIR)

	print "%d docs to %s" % (len(docIds), mappingsFile)
	counter = 0
	counterPos = 0
	counterNeg = 0
	for did, label in zip(docIds, labels):
		path = pathsDict.get(str(did) + ".txt")
		if path == None:
			path = pathsDict2016[str(did) + ".txt"]
		words = getWords(path)
		if len(words) < MIN_DOC_LEN and ignoreShortDocs:
			continue

		words = words[:MAX_DOC_LEN]
		
		######################## NN
#		mappings = [VOCAB_MAP[word] for word in words[:MAX_NN_DOC_LEN]]
#		mappings += [0] * (MAX_NN_DOC_LEN - len(mappings)) ### 0 for PADDING
#		mappingsOut.write("%s\n" % " ".join(map(str, mappings)))
#		if label == 1:
#			nnLabelsOut.write("1 0\n")
#		else: #label == 0 or -1
#			nnLabelsOut.write("0 1\n")
		#######################

		wordsOut.write("%s\n" % " ".join(words))
		
		labelsOut.write("%d\n" % label)
		if label == 1:
			counterPos+=1
		else:
			counterNeg+=1

		idsOut.write("%d\n" % did)

		counter += 1
		if counter % 10000 == 0:
			print "Done %d docs, %d pos, %d neg" % (counter, counterPos, counterNeg)

	print "--------------\nTotal docs %d, %d pos, %d neg\n\n" % (counter, counterPos, counterNeg)
	wordsOut.close()
	mappingsOut.close()
	labelsOut.close()
	nnLabelsOut.close()
	idsOut.close()




def getLabels(pos, neg):
	return [1] * len(pos) + [-1] * len(neg)

def writeIrResAndQrelsDataset():
	print "Writing ir res and qrels dataset"
	resDir = os.path.join(CLASSIFICATION_DATA_DIR, "res-and-qrels")

	positiveQrelsAllDocs = utils.getRelevantQrelDocIdsAllCategories(qrels2014) | utils.getRelevantQrelDocIdsAllCategories(qrels2015) \
							| utils.getRelevantQrelDocIdsAllCategories(qrels2016)
	negativeQrelsDocIds = set(list(qrelsDocIds - positiveQrelsAllDocs)[:len(positiveQrelsAllDocs)])

	print "Lengths (resultsDocIds: %d, positiveQrelsDocIds: %d, negativeQrelsDocIds: %d)" % (\
		len(resultsDocIds), len(positiveQrelsAllDocs), len(negativeQrelsDocIds)
	)

	resAndQrelsDocIds = resultsDocIds | positiveQrelsAllDocs | negativeQrelsDocIds
	writeDocsData(resAndQrelsDocIds, [-1] * len(resAndQrelsDocIds),	os.path.join(resDir, "words.txt"), \
													  				os.path.join(resDir, "mappings.txt"), \
													  				os.path.join(resDir, "labels.txt"), \
															  		os.path.join(resDir, "labels-nn.txt"), \
															  		os.path.join(resDir, "ids.txt"))

#def writeIrResAndAllQrelsDataset():
#	print "Writing ir and all qrels dataset"
#	resDir = os.path.join(CLASSIFICATION_DATA_DIR, "res-and-all-qrels")
#	didsToWrite = resultsDocIds | qrelsDocIds
#	writeDocsData(didsToWrite, [-1] * len(didsToWrite),	os.path.join(resDir, "words.txt"), \
#										  				os.path.join(resDir, "mappings.txt"), \
#										  				os.path.join(resDir, "labels.txt"), \
#												  		os.path.join(resDir, "labels-nn.txt"), \
#												  		os.path.join(resDir, "ids.txt"))


def writeHedgesDatasets(category):
	positiveSamples = codecs.open(os.path.join("data/hedges", category + "-analyzed.txt"), "r", "utf-8").read().splitlines()
	negativeSamples = codecs.open(os.path.join("data/hedges", "others-analyzed.txt"), "r", "utf-8").read().splitlines()
	negativeSamples = negativeSamples[:len(positiveSamples)]
	positiveLen = len(positiveSamples)
	negativeLen = len(negativeSamples)
	
	print "Positive samples:", positiveLen, ", negative samples:", negativeLen
	
	samples = positiveSamples + negativeSamples 
	labels = [1] * positiveLen + [-1] * negativeLen
	
	mappingsOut = open("data/" + category + "/train/mappings-hedges.txt", "w")
	nnLabelsOut = open("data/" + category + "/train/labels-nn-hedges.txt", "w")
	count = 1
	unmappedWords = 0
	totalWords = 0
	unmappedDocs = 0
	totalDocs = 0
	for sampleLine, label in zip(samples, labels):
		words = sampleLine.split()
		words = words[:MAX_NN_DOC_LEN]
		
		mappings = []
		foundUnmapped = False
		for word in words:
			mapping = VOCAB_MAP.get(word, 0)
			if mapping == 0:
				print "Doc #%d: word %s does not have mapping, using 0" % (count, word)
				unmappedWords += 1
				foundUnmapped = True
			mappings.append(mapping)

		if foundUnmapped:
			unmappedDocs += 1
		
		totalWords += len(words)
		totalDocs += 1
		
		mappings += [0] * (MAX_NN_DOC_LEN - len(mappings)) ### 0 for PADDING
		mappingsOut.write("%s\n" % " ".join(map(str, mappings)))
		if label == 1:
			nnLabelsOut.write("1 0\n")
		else: #label == 0 or -1
			nnLabelsOut.write("0 1\n")
		
		count += 1
			
	mappingsOut.close()
	nnLabelsOut.close()
	
	print "%d/%d unmapped words in %d/%d documents" % (unmappedWords, totalWords, unmappedDocs, totalDocs)

def writeDatasets(category):

	### UNCOMMENT FOR NEW DOCS
#	posIds, negIds = getTrainingAndTestIdsForCategory(category)
#	trainPos, testPos = splitTrainTest(posIds)
#	trainNeg, testNeg = splitTrainTest(negIds)
#	trainIds = trainPos + trainNeg
#	testIds = testPos + testNeg
#	trainLabels = getLabels(trainPos, trainNeg)
#	testLabels = getLabels(testPos, testNeg)
	###

	categoryDir = os.path.join(CLASSIFICATION_DATA_DIR, category)
	trainDir = os.path.join(categoryDir, "train")
	testDir = os.path.join(categoryDir, "test")
	
	### UNCOMMENT FOR SAME DOCS
	trainIds = utils.readInts(os.path.join(trainDir, "ids.txt"))
	testIds = utils.readInts(os.path.join(testDir, "ids.txt"))
	trainLabels = utils.readInts(os.path.join(trainDir, "labels.txt"))
	testLabels = utils.readInts(os.path.join(testDir, "labels.txt"))
	###

	print "Writing train mappings"
	writeDocsData(trainIds, trainLabels, os.path.join(trainDir, "words.txt"), \
										os.path.join(trainDir, "mappings.txt"), \
										os.path.join(trainDir, "labels.txt"), \
										os.path.join(trainDir, "labels-nn.txt"), \
										os.path.join(trainDir, "ids.txt"), \
										ignoreShortDocs=True)

	print "Writing test mappings"
	writeDocsData(testIds, testLabels, os.path.join(testDir, "words.txt"), \
										os.path.join(testDir, "mappings.txt"), \
										os.path.join(testDir, "labels.txt"), \
										os.path.join(testDir, "labels-nn.txt"), \
										os.path.join(testDir, "ids.txt"), \
										ignoreShortDocs=True)

#writeIrResultsIds()

#VOCAB_MAP = readVocabMap()
#writeEmbeddings()

#writeIrResAndAllQrelsDataset()
writeIrResAndQrelsDataset()

#writeDatasets(CATEGORY)
#writeHedgesDatasets(CATEGORY)


	
