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
EMBED_SIZE = 100

CATEGORY = sys.argv[1]

CLASSIFICATION_DATA_DIR = "data/"
SENTENCES_DIR = os.path.join(CLASSIFICATION_DATA_DIR, "sentences")

qrels2014 = utils.readQrels2014()
qrels2015 = utils.readQrels2015()
qrelsDocIds = set(utils.getQrelsDocIds(qrels2014)) | set(utils.getQrelsDocIds(qrels2015))

#positiveQrelsDocIds = utils.getRelevantQrelDocIdsForCategory(qrels2014, CATEGORY) |\
#					  utils.getRelevantQrelDocIdsForCategory(qrels2015, CATEGORY)

results2014AllModels = utils.readResultsAllModels(2014)
results2015AllModels = utils.readResultsAllModels(2015)

resultsDocIds = map(utils.getResultsDocIds, results2014AllModels) + map(utils.getResultsDocIds, results2015AllModels)
resultsDocIds = set.union(*map(set, resultsDocIds))

#nonQrelsOrResultsDids = utils.VALID_DOC_IDS - resultsDocIds -positiveQrelsDocIds #- qrelsDocIds

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
	return readPmcIds(os.path.join(catDir, "positive-pmc-ids-relaxed-more.txt"))

def getNegativePmcIds(category):
	catDir = os.path.join(CLASSIFICATION_DATA_DIR, category, "positive-ids")
	return readPmcIds(os.path.join(catDir, "negative-pmc-ids.txt"))

def getTrainingAndTestIdsForCategory(category):
	positiveDocIds = getPositivePmcIds(category) & utils.VALID_DOC_IDS # nonQrelsOrResultsDids
	negativeDocIds = utils.VALID_DOC_IDS - getPositiveRelaxedPmcIds(category)   #nonQrelsOrResultsDids - getPositiveRelaxedPmcIds(category)
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
    model = gensim.models.Word2Vec.load("../word2vec/model")
    inverseMap = {index: word for word, index in VOCAB_MAP.items()}
    out = open("nn/embeddings.txt", "w")

    out.write("%s\n" % ("0.0 " * EMBED_SIZE)) # zeros for <PAD/> (index 0)
    for index in range(1, 1 + len(inverseMap)):
    	word = inverseMap[index]
    	embedding = " ".join(str(x) for x in model[word])
        out.write("%s\n" % embedding)
        if (index % 100000 == 0):
            print "Wrote up to word %d" % index

    out.close()

def writeDocsData(docIds, labels, wordsFile, mappingsFile, labelsFile, nnLabelsFile, idsFile, ignoreShortDocs=False):
	wordsOut = codecs.open(wordsFile, "w", "utf-8")
	mappingsOut = codecs.open(mappingsFile, "w", "utf-8")
	labelsOut = open(labelsFile, "w")
	nnLabelsOut = open(nnLabelsFile, "w")
	idsOut = open(idsFile, "w")

	fnames = map(lambda did: str(did) + ".txt.sent.analyzed", docIds)
	pathsDict = utils.getFilePaths(fnames, SENTENCES_DIR)

	print "%d docs to %s" % (len(docIds), mappingsFile)
	counter = 0
	counterPos = 0
	counterNeg = 0
	for did, label in zip(docIds, labels):
		path = pathsDict[str(did) + ".txt.sent.analyzed"]
		words = getWords(path)
		if len(words) < MIN_DOC_LEN and ignoreShortDocs:
			continue

		######################## NN
		words = words[:MAX_DOC_LEN]
		mappings = [VOCAB_MAP[word] for word in words]
		mappings += [0] * (MAX_DOC_LEN - len(mappings))
		mappingsOut.write("%s\n" % " ".join(map(str, mappings)))
		if label == 1:
			nnLabelsOut.write("1 0\n")
		else: #label == 0 or -1
			nnLabelsOut.write("0 1\n")
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
	return [1] * len(pos) + [0] * len(neg)

#def writeRelevantQrelDocsDataset():
#	print "Writing relevant qrel docs dataset"
#	resDir = os.path.join(CLASSIFICATION_DATA_DIR, "relevant-qrel-docs")
#	docIds = getRelevantQrelDocIds(qrels2014) | getRelevantQrelDocIds(qrels2015)
#	writeDocsData(docIds, [1] * len(docIds),	os.path.join(resDir, "words.txt"), \
#								  				os.path.join(resDir, "mappings.txt"), \
#								  				os.path.join(resDir, "labels.txt"), \
#										  		os.path.join(resDir, "labels-nn.txt"), \
#										  		os.path.join(resDir, "ids.txt"))

def writeIrResAndQrelsDataset():
	print "Writing ir res and qrels dataset"
	resDir = os.path.join(CLASSIFICATION_DATA_DIR, "res-and-qrels")

	positiveQrelsAllDocs = utils.getRelevantQrelDocIdsAllCategories(qrels2014) | utils.getRelevantQrelDocIdsAllCategories(qrels2015)
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

def writeDatasets(category):
	posIds, negIds = getTrainingAndTestIdsForCategory(category)
	trainPos, testPos = splitTrainTest(posIds)
	trainNeg, testNeg = splitTrainTest(negIds)
	trainLabels = getLabels(trainPos, trainNeg)
	testLabels = getLabels(testPos, testNeg)

	categoryDir = os.path.join(CLASSIFICATION_DATA_DIR, category)
	trainDir = os.path.join(categoryDir, "train")
	testDir = os.path.join(categoryDir, "test")

	print "Writing train mappings"
	writeDocsData(trainPos + trainNeg, trainLabels, os.path.join(trainDir, "words.txt"), \
													os.path.join(trainDir, "mappings.txt"), \
													os.path.join(trainDir, "labels.txt"), \
													os.path.join(trainDir, "labels-nn.txt"), \
													os.path.join(trainDir, "ids.txt"), \
													ignoreShortDocs=True)

	print "Writing test mappings"
	writeDocsData(testPos + testNeg, testLabels, os.path.join(testDir, "words.txt"), \
												os.path.join(testDir, "mappings.txt"), \
												os.path.join(testDir, "labels.txt"), \
												os.path.join(testDir, "labels-nn.txt"), \
												os.path.join(testDir, "ids.txt"), \
												ignoreShortDocs=True)

VOCAB_MAP = readVocabMap()
#writeEmbeddings()
#writeRelevantQrelDocsDataset()

#writeIrResAndQrelsDataset()
writeDatasets(CATEGORY)
