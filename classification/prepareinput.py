#!/bin/python

import sys
import os
import random
import codecs
import gensim

sys.path.insert(0, "../utils/")
import utils

CLASSIFICATION_DATA_DIR = "data/"
SENTENCES_DIR = os.path.join(CLASSIFICATION_DATA_DIR, "sentences")

qrels2014 = utils.readQrels2014()
qrels2015 = utils.readQrels2015()
qrelsDocIds = set(utils.getQrelsDocIds(qrels2014)) | set(utils.getQrelsDocIds(qrels2015))

results2014 = utils.readResults2014()
results2015A = utils.readResults2015A()
results2015B = utils.readResults2015B()
resultsDocIds = set(utils.getResultsDocIds(results2014)) | set(utils.getResultsDocIds(results2015A)) | set(utils.getResultsDocIds(results2015B))

nonQrelsOrResultsDids = utils.VALID_DOC_IDS - qrelsDocIds - resultsDocIds

def readPmcIds(pmcIdsFile):
	return set(map(lambda pmcid: int(pmcid[3:]), open(pmcIdsFile).read().split()))


def getPositivePmcIds(category):
	catDir = os.path.join(CLASSIFICATION_DATA_DIR, category)
	posIds = readPmcIds(os.path.join(catDir, "positive-pmc-ids.txt"))
	if category == "diag":
		posIds |= readPmcIds(os.path.join(catDir, "diag-services.txt"))
	
	if category == "test":
		posIds |= readPmcIds(os.path.join(catDir, "caries-tests.txt"))
		posIds |= readPmcIds(os.path.join(catDir, "diag-test-and-procedures.txt"))
		posIds |= readPmcIds(os.path.join(catDir, "psycho-tests.txt"))
		posIds |= readPmcIds(os.path.join(catDir, "tox-tests.txt"))
	#if category == "treat":
	#	posIds |= readPmcIds(os.path.join(catDir, "treatment-outcome.txt"))
	#	posIds |= readPmcIds(os.path.join(catDir, "therapy.txt"))
	#	posIds |= readPmcIds(os.path.join(catDir, "therapeutic-use.txt"))
		
	return posIds	

def getTrainingAndTestIdsForCategory(category):
	positiveDocIds = getPositivePmcIds(category)
	positiveDocIds &= nonQrelsOrResultsDids
	negativeDocIds = nonQrelsOrResultsDids - positiveDocIds
	positiveDocIds = list(positiveDocIds)
	negativeDocIds = list(negativeDocIds)
	print "Total pos %d, total neg %d" % (len(positiveDocIds), len(negativeDocIds))
	random.shuffle(positiveDocIds)
	random.shuffle(negativeDocIds)
	numIds = min(25000, len(positiveDocIds), len(negativeDocIds))
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
	for line in codecs.open("nn/vocmap.txt"), "r", "utf-8"):
		parts = line.split()
		vocabMap[parts[0]] = int(parts[1])
	return vocabMap

MIN_DOC_LEN = 200
MAX_DOC_LEN = 10000
EMBED_SIZE = 100

# !! also account for <PAD>
# the w2v floats are truncated to 6 digits
def writeEmbeddings():
    print "Reading word2vec model"
    model = gensim.models.Word2Vec.load("../word2vec/model")
    inverseMap = {index: word for word, index in VOCAB_MAP.items()}
    out = open("nn/embeddings.txt", "w")
    
    out.write("%s\n" % ("0.0 " * EMBED_SIZE)) # zeros for <PAD/> (index 0)
    for index in range(1, 1 + len(inverseMap))
    	word = inverseMap[index]
    	embedding = " ".join(str(x) for x in model[word])
        out.write("%s\n" % embedding)
        if (index % 100000 == 0):
            print "Wrote up to word %d" % index

    out.close()

def writeDocsData(docIds, labels, wordsFile, mappingsFile, labelsFile, idsFile, ignoreShortDocs=False):
	wordsOut = codecs.open(wordsFile, "w", "utf-8")
	mappingsOut = codecs.open(mappingsFile, "w", "utf-8")
	labelsOut = open(labelsFile, "w")
	idsOut = open(idsFile, "w")
	
	fnames = map(lambda did: str(did) + ".txt.sent", docIds)
	pathsDict = utils.getFilePaths(fnames, SENTENCES_DIR)
	
	print "%d docs to %s" % (len(docIds), mappingsFile)
	counter = 0
	for did, label in zip(docIds, labels):
		path = pathsDict[str(did) + ".txt.sent"]
		words = getWords(path)[:MAX_DOC_LEN]
		if len(words) < MIN_DOC_LEN and ignoreShortDocs:
			continue
		mappings = [VOCAB_MAP[word] for word in words]
		mappings += [0] * (MAX_DOC_LEN - len(mappings))
		mappingsOut.write("%s\n" % " ".join(mappings))
		wordsOut.write("%s\n" % " ".join(words))
		labelsOut.write("%s\n" % label)
		idsOut.write("%d\n" % did)
		
		counter += 1
		if counter % 10000 == 0:
			print "Done %d docs" % counter
	
	print "--------------\nTotal docs %d\n\n" % counter
	wordsOut.close()
	mappingsOut.close()
	labelsOut.close()
	idsOut.close()


def getLabels(pos, neg):
	return ["1"] * len(pos) + ["0"] * len(neg)

def writeIrResDataset():
	print "Writing ir res mappings"
	resDir = os.path.join(CLASSIFICATION_DATA_DIR, "ir-res")
	writeDocsData(resultsDocIds, [-1] * len(resultsDocIds),	os.path.join(resDir, "words.txt"), \
													  		os.path.join(resDir, "mappings.txt"), \
													  		os.path.join(resDir, "labels.txt"), \
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
													os.path.join(trainDir, "ids.txt"), \
													ignoreShortDocs=True)

	print "Writing test mappings"
	writeDocsData(testPos + testNeg, testLabels, os.path.join(testDir, "words.txt"), \
												os.path.join(testDir, "mappings.txt"), \
												os.path.join(testDir, "labels.txt"), \
												os.path.join(testDir, "ids.txt"), \
												ignoreShortDocs=True)

VOCAB_MAP = readVocabMap()
writeIrResDataset()
writeDatasets(sys.argv[1])
