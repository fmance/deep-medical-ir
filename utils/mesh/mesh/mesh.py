import os
import pprint
import csv
import sys
import subprocess
from collections import Counter

sys.path.insert(0, "..")
import utils

classId = sys.argv[1]

qrels2014 = utils.readQrels2014()
qrels2015 = utils.readQrels2015()

def getRelevantBothYears(classId):
	relevant = utils.getRelevantQrelDocIdsForCategory(qrels2014, classId) | utils.getRelevantQrelDocIdsForCategory(qrels2015, classId)
	return utils.VALID_DOC_IDS & relevant

def getIdMapping(pmcids):
	mapping = {}
	csvreader = csv.reader(open("../../data/doc-ids/PMC-ids.csv"), delimiter=',')
	next(csvreader)
	for row in csvreader:
		pmcid = row[8]
		assert pmcid.startswith("PMC")
		pmcid = int(pmcid[3:])
		pmid = row[9]
		if pmid != "" and pmcid in pmcids:
			mapping[pmcid] = int(pmid)
	return mapping

def getMeshTerms():
	relevant = getRelevantBothYears(classId)
	mappings = getIdMapping(relevant)
	print len(mappings)

	pmids = ",".join(map(str, mappings.values()))

	meshCommand = "efetch -db pubmed -id " + pmids + " -format xml | xtract -pattern PubmedArticle -PMID MedlineCitation/PMID " + \
					"-group MeshHeading " + \
					  "-block MeshHeading -match QualifierName " + \
						"-subset DescriptorName -TERM \"DescriptorName\" -MAJR \"@MajorTopicYN\" " + \
						"-subset QualifierName -tab \"\n\" " + \
						  "-element \"&PMID\",\"&TERM\",\"&MAJR\",QualifierName,\"@MajorTopicYN\" " + \
					  "-block MeshHeading -avoid QualifierName " + \
						"-subset DescriptorName -tab \"\n\" " + \
						  "-element \"&PMID\",DescriptorName,\"@MajorTopicYN\""
	print "Calling efetch"			  
	output = subprocess.Popen([meshCommand], stdout=subprocess.PIPE, shell=True).communicate()[0]
	print "done"
	out = open("mesh-" + classId + ".txt", "w")
	out.write(output)
	out.close()
	
def readMeshTerms():
	foundIds = []
	meshTerms = []
	for line in open("mesh-" + classId + ".txt"):
		parts = line.strip().split("\t")
		#if parts[2] == "Y" or (len(parts) == 5 and parts[4] == "Y"):
		meshTerms.append(parts[1])
#		if len(parts) == 5:
#			if parts[4] == "Y":
#				meshTerms.append(parts[3])
		foundIds.append(int(parts[0]))
	return set(foundIds), Counter(meshTerms)

#getMeshTerms()
foundIds, meshTerms = readMeshTerms()
pprint.pprint(meshTerms.most_common(20))
print len(foundIds)
