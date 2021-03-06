import os
import csv
import sys
from collections import defaultdict

sys.path.insert(0, "../utils/")
import utils

def getPmidToPmcidMapping():
	mapping = {}
	csvreader = csv.reader(open("../data/doc-ids/PMC-ids.csv"), delimiter=',')
	next(csvreader)
	counter = 0
	for row in csvreader:
		pmcid = row[8]
		pmcid = int(pmcid[3:])
		pmid = row[9]
		if pmid == "":
			continue
		pmid = int(pmid)
		mapping[pmid] = pmcid
		counter += 1
		if counter % 1000000 == 0:
			print counter
	return mapping
	
def convertResultsDocIdsToPmids():
	mapping = getPmidToPmcidMapping()
	pmcids = set(utils.readInts("data/res-and-qrels/ids.txt"))
	filteredMap = [(pmid, pmcid) for pmid,pmcid in mapping.items() if pmcid in pmcids]
	out = open("data/hedges/results-pmids.txt", "w")
	for pmid, pmcid in filteredMap:
		out.write("%d %d\n" % (pmid, pmcid))
	out.close()
#convertResultsDocIdsToPmids()
	
MAPPING = getPmidToPmcidMapping()
def convertPmidFileToPmcidFile(inputFile):
	pmids = utils.readInts(inputFile)
	pmcids = []
	
	valid = 0
	for pmid in pmids:
		pmcid = MAPPING.get(pmid, -1)
		if pmcid in utils.VALID_DOC_IDS:
			valid += 1
			pmcids.append(pmcid)
#		else:
#			pmcids.append(-1)
	
	out = open(inputFile + ".converted-to-pmcids.txt", "w")
	for pmcid in pmcids:
		out.write("%d\n" % pmcid)
	out.close()
	print "Valid ids: ", valid

convertPmidFileToPmcidFile("data/hedges/diag-analyzed-ids.txt")
convertPmidFileToPmcidFile("data/hedges/treat-analyzed-ids.txt")
convertPmidFileToPmcidFile("data/hedges/others-analyzed-ids.txt")

def readHedgesCSV():
	diag = []
	treat = []
	allCat = []
	reader = csv.reader(open("../../hedges/hedges.csv"), delimiter=",")
	next(reader)
	for row in reader:
		pmid = int(row[0])
		cls = row[3]
		if cls == "D":
			diag.append(pmid)
		if cls == "Tr":
			treat.append(pmid)
		allCat.append(pmid)
	return set(diag), set(treat), set(allCat)

#diag, treat, allCat = readHedgesCSV()
#others = allCat - diag - treat

#print len(diag), len(treat), len(others)
#out = open("data/hedges/pmids-others.txt", "w")
#for pmid in others:
#	out.write("%d\n" % pmid)
#out.close()

#mapping = getPmidToPmcidMapping()
#others = utils.readInts("data/mesh-tagged-pmids.txt")
#pmcids = [mapping[pmid] for pmid in others if pmid in mapping]
#print len(pmcids)
#out = open("data/mesh-tagged-pmcids.txt", "w")
#for pmcid in pmcids:
#	out.write("%d\n" % pmcid)
#out.close()
	
	

