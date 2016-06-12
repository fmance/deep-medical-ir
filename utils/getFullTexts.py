#!/usr/bin/python

import os
import sys
import codecs
import time
import re
import utils
import csv
import pprint
import ftplib

DOC_IDS_DIR = os.path.join(utils.DATA_DIR, "doc-ids")

def getPdfOnlyIds():
	pmcids = open(os.path.join(DOC_IDS_DIR, "pdf-only.txt")).read().split()
	return set(map(lambda pmcid: int(pmcid[3:]), pmcids)) & utils.VALID_DOC_IDS
	
def getFilePathMap(pmcids):
	fileList = open(os.path.join(DOC_IDS_DIR, "file_list.pdf.csv"))
	pathMap = {}
	
	reader = csv.reader(fileList)
	next(reader)
	
	good = 0
	bad = 0
	
	for row in reader:
		pmcid = int(row[2][3:])
		if pmcid not in pmcids:
			continue
	
		citation = row[1]
		m=re.search("([\w \(\)\[\]\.]+)\. ?(\d+)? ?([\w-]+)? ?(\d+)? ?([\w-]+)?; ?([\w\(\) \,\.-]+)?:(.+)", citation)
		
		if not m:
			print citation
		
		journal = m.group(1).replace(" ", "_").replace(".", "_")
		year = m.group(2)
		month = m.group(3)
		day = m.group(4)
		month2 = m.group(5)
		vol = m.group(6)
		if vol:
			vol = vol.replace(" ", "_").replace(",", "").replace(".", "")
		issue = m.group(7).replace(".", "_").replace("/", "_")
		
		filename = "_".join([comp for comp in [journal, year, month, day, month2, vol, issue] if comp is not None]) + ".txt"
		
		path = os.path.join(utils.DATA_DIR, "plaintext-from-pmc", journal, filename)

		if os.path.isfile(path):
			pathMap[pmcid] = path
			good += 1
		else:
			bad += 1
#			print "\n------------------------"
#			print "ERRROR", path
#			print row
#			print "---------------------------"		
		
			
	print "\n", good, bad, "\n"
	
	return pathMap
	
def replaceFiles():
	pathMap = getFilePathMap(getPdfOnlyIds())
	
	docIds = pathMap.keys()
	fnames = map(lambda did: str(did) + ".txt", docIds)
	pathsDict = utils.getFilePaths(fnames, utils.PLAINTEXT_DIR)
	
	counter = 0
	
	for did, path in pathMap.items():
		originalLocation = pathsDict[str(did) + ".txt"]
#		originalTextLines = codecs.open(originalLocation, "r", "utf-8").readlines()
		fullTextLines = codecs.open(pathMap[did], "r", "utf-8").readlines()
		fullTextLinesNoRefs = []
		for line in fullTextLines:
			if len(line.split()) == 1 and bool(re.match("ref", line, re.I)):
				break
			fullTextLinesNoRefs.append(line)

		fullOut = codecs.open(originalLocation + ".full", "w", "utf-8")
		for line in fullTextLinesNoRefs:
			fullOut.write(line)
		fullOut.close()
		
		counter+=1
		if counter % 1000 == 0:
			print counter
			
	print "Done", counter, "files"

replaceFiles()
	
#pathMap = getFilePathMap(getPdfOnlyIds())
#ids = set(pathMap.keys())
#qrel2014Ids = utils.getRelevantQrelDocIdsAllCategories(utils.readQrels2014())
#qrel2015Ids = utils.getRelevantQrelDocIdsAllCategories(utils.readQrels2015())
#qrelIds = set(qrel2014Ids) | set(qrel2015Ids)

#print ids & qrelIds


