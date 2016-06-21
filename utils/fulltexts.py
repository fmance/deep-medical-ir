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
	fileList = open(os.path.join(DOC_IDS_DIR, "file_list.csv"))
	pathMap = {}
	
	reader = csv.reader(fileList)
	next(reader)
	
	good = 0
	notfound = 0
	bad = 0
	
	for row in reader:
		pmcid = int(row[2][3:])
		if pmcid not in pmcids:
			continue
	
		citation = row[1]
		m=re.search("([\w,/ \(\)\[\]\.-]+)\. ?(\d+)? ?([\w-]+)? ?(\d+)? ?([\w-]+)?; ?([\w\(\) \,\.-]+)?:(.+)", citation)
		
		if not m:
			print citation
		
		journal = m.group(1).replace(" ", "_").replace(".", "_").replace("__", "_")
		year = m.group(2)
		month = m.group(3)
		day = m.group(4)
		month2 = m.group(5)
		vol = m.group(6)
		if vol:
			vol = vol.replace(" ", "_").replace(",", "").replace(".", "")
		issue = m.group(7).replace(".", "_").replace("/", "_").replace(" ", "_")
		
		filename = "_".join([comp for comp in [journal.replace(",", "").replace("/", "_"),
												year, month, day, month2, vol, issue] if comp is not None]) + ".txt"
		filename = filename.replace(":", "_").replace("__", "_")
		
		if journal == "Ecography_(Cop_)":
			journal = "Ecography_(Cop"
		
		path = os.path.join(utils.DATA_DIR, "plaintext-from-pmc", journal, filename)

		if os.path.isfile(path):
			pathMap[pmcid] = path
			good += 1
		elif "Anc_Sci_Life" in path \
				or "J_Korean_Med_Sci" in path \
				or "Genet_Sel_Evol" in path \
				or "Sarcoma" in path \
				or "Springerplus" in path \
				or "Agric_For_Entomol" in path \
				or "Br_J_Cancer" in path \
				or "COMSIG_Rev" in path \
				or "Australas_Chiropr_Osteopathy" in path:
			notfound += 1
		else:
			bad += 1
			print "\n------------------------"
			print "ERRROR", path
			print row
			print "---------------------------"		
		
			
	print "\n", good, notfound, bad, "\n"
	
	return pathMap
	
def writeFullFiles():
	pathMap = getFilePathMap(getPdfOnlyIds())
	
	docIds = pathMap.keys()
	fnames = map(lambda did: str(did) + ".txt", docIds)
	pathsDict = utils.getFilePaths(fnames, utils.PLAINTEXT_DIR)
	
	counter = 0
	for did, path in pathMap.items():
		originalLocation = pathsDict[str(did) + ".txt"]
		originalTextLines = codecs.open(originalLocation, "r", "utf-8").readlines()
		fullTextLines = codecs.open(pathMap[did], "r", "utf-8").readlines()
		outputLines = [originalTextLines[0]] + ["\n\n"]
		for line in fullTextLines:
			if "==== Refs" in line or line == "References\n" or line == "REFERENCES\n":
				break
			outputLines.append(line)

		out = codecs.open(originalLocation + ".full", "w", "utf-8")
		for line in outputLines:
			out.write(line)
		out.close()
		
		counter += 1
		if counter % 1000 == 0:
			print "Done", counter, "files"
	print "Done", counter, "files"

def writePathMap():
	pathMap = getFilePathMap(getPdfOnlyIds())
	out = open("../data/doc-ids/pdf-only-path-map.txt", "w")
	for pmcid, path in pathMap.items():
		out.write("%d %s\n" % (pmcid, path))
	out.close()

writeFullFiles()
#writePathMap()

