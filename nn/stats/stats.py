#!/bin/python

import codecs, os
from collections import defaultdict, Counter
import time
import regex, math
import numpy as np

STATS_FILE = "stats.txt"
QUERIES_2014 = "../../data/topics-2014.xml.plaintext"
QUERIES_2015 = "../../data/topics-2015-A.xml.plaintext"
DOCS_DIR = "../../data/nn/qrel-and-res-docs/"
DOC_IDS_FILE = DOCS_DIR + "ids.txt"
DOC_TERMS_FILE = "doc-terms.txt"
DOC_TITLE_TERMS_FILE = "doc-title-terms.txt"
QUERIES_2014_TERMS_FILE = "query-2014-terms.txt"
QUERIES_2015_TERMS_FILE = "query-2015-terms.txt"
FEATURES_2014 = "features-2014.txt"
FEATURES_2015 = "features-2015.txt"

k1 = 1.2
b = 0.75

validDocIds = set(map(int, open("../../data/valid-doc-ids.txt").read().split()))

stopWords = set(open("stop_words.txt").read().split())

def stripAndLower(s):
    return regex.sub(ur"\P{Latin}", " ", s).lower()

def filterTerms(terms):
    return [t for t in terms if t not in stopWords]

def getDocTerms(path):
    text = codecs.open(path, "r", "utf-8").read()
    terms = stripAndLower(text).split()
    return filterTerms(terms)

def getDocTitleTerms(path):
    text = codecs.open(path, "r", "utf-8").readlines()[0]
    terms = stripAndLower(text).split()
    return filterTerms(terms)

def getCollectionStats():
    docFreq = defaultdict(int)
    numDocs = 0
    numTerms = 0
    start = time.time()
    for sdir in ["../../data/plaintext/" + d for d in ["00", "01", "02", "03"]]:
        for ssdir in [os.path.join(sdir, ssdir) for ssdir in sorted(os.listdir(sdir))]:
            for fname in [os.path.join(ssdir, fname) for fname in sorted(os.listdir(ssdir))]:
                terms = getDocTerms(fname)
                numDocs += 1
                numTerms += len(terms)
                for term in set(terms):
                    docFreq[term] += 1
                if numDocs % 1000 == 0:
                    print "%d docs (%s) in %.2f minutes" % (numDocs, ssdir, (time.time() - start)/60.0)
    return docFreq, numDocs, float(numTerms)/numDocs

def writeCollectionStats(statsFile):
    docFreq, numDocs, avgDocLen = getCollectionStats()
    out = codecs.open(statsFile, "w", "utf-8")
    out.write("%d %f\n" % (numDocs, avgDocLen))
    for term, freq in docFreq.items():
        out.write("%s %d\n" % (term, freq))
    out.close()

def readCollectionStats(statsFile):
    print "Reading collection stats"
    lines = codecs.open(statsFile, "r", "utf-8").readlines()
    line0parts = lines[0].split()
    numDocs = int(line0parts[0])
    avgDocLen = float(line0parts[1])
    docFreq = defaultdict(int)
    for line in lines[1:]:
        parts = line.split()
        term = parts[0]
        freq = int(parts[1])
        docFreq[term] = freq
    print "Done"
    return docFreq, numDocs, avgDocLen

# See also https://lucene.apache.org/core/5_5_0/core/org/apache/lucene/search/similarities/BM25Similarity.html
def bm25(qterms, docTfs, docLen):
    score = 0.0
    for qterm in qterms:
        tf = docTfs[qterm]
        df = docFreq[qterm]
        idf = math.log(1 + (numDocs - df + 0.5)/(df + 0.5))
        norm = k1 * (1.0 - b + b * float(docLen)/avgDocLen)
        score += idf * tf * (k1 + 1) / (tf + norm)
    return score

def stats(ls):
    return [sum(ls), min(ls), max(ls), np.mean(ls), np.var(ls)]

# See also https://lucene.apache.org/core/5_5_0/core/org/apache/lucene/search/similarities/TFIDFSimilarity.html
def tfidfFeatures(qterms, docTfs, docLen):
    score = 0.0
    ssw = 0.0
    matches = 0.0
    idfSum = 0.0
    tfs = []
    tfidfs = []
    for qterm in qterms:
        tf = math.sqrt(docTfs[qterm])
        idf = 1 + math.log(float(numDocs)/(docFreq[qterm] + 1))
        idf2 = idf * idf
        ssw += idf2
        matches += int(tf > 0)
        tfidf = tf * idf2
        score += tfidf 
        idfSum += idf
        tfs.append(tf)
        tfidfs.append(tfidf)
    coord = matches/len(qterms)
    queryNorm = 1.0/math.sqrt(ssw)
    docNorm = 1.0/math.sqrt(1 + docLen)
    score *= (coord * queryNorm * docNorm)
    tfsNormalized = [tf/(1 + docLen) for tf in tfs]
    
    return [score, matches, coord, docLen, idf] + stats(tfs) + stats(tfsNormalized) + stats(tfidfs)

def getFeaturesQueryDoc(did, qterms, docTfs):
    docLen = sum(docTfs.values())
    return [bm25(qterms, docTfs, docLen)] + tfidfFeatures(qterms, docTfs, docLen)

def getQueryTermsDict(queryFile):
    queries = {}
    for line in codecs.open(queryFile, "r", "utf-8"):
        parts = line.split()
        qid = int(parts[0])
        qtext = " ".join(parts[1:])
        qterms = filterTerms(stripAndLower(qtext).split())
        queries[qid] = qterms
    return queries

def writeQueryTermDict(queryFile, outFile):
    out = codecs.open(outFile, "w", "utf-8")
    for qid, queryTerms in getQueryTermsDict(queryFile).items():
        out.write("%d " % qid)
        out.write(" ".join(queryTerms))
        out.write("\n")
    out.close()

def writeDocTermsDict(docIdsFile, docsDir, outFile):
    docIds = map(int, open(docIdsFile).readlines())
    out = codecs.open(outFile, "w", "utf-8")
    count = 0
    for did in docIds:
        docTerms = getDocTerms(os.path.join(docsDir, str(did) + ".txt"))
        out.write("%d " % did)
        out.write(" ".join(docTerms))
        out.write("\n")
        count += 1
        if count % 1000 == 0:
            print "%d/%d" % (count, len(docIds))
    out.close()

def writeDocTitleTermsDict(docIdsFile, docsDir, outFile):
    docIds = map(int, open(docIdsFile).readlines())
    out = codecs.open(outFile, "w", "utf-8")
    count = 0
    for did in docIds:
        docTerms = getDocTitleTerms(os.path.join(docsDir, str(did) + ".txt"))
        out.write("%d " % did)
        out.write(" ".join(docTerms))
        out.write("\n")
        count += 1
        if count % 1000 == 0:
            print "%d/%d" % (count, len(docIds))
    out.close()

def readTermFreq(docTermsFile):
    print "Reading term frequencies"
    termFreq = {}
    counter = 0
    for line in codecs.open(docTermsFile, "r", "utf-8"):
        parts = line.split()
        did = int(parts[0])
        tfs = defaultdict(int)
        for term in parts[1:]:
            tfs[term] += 1
        termFreq[did] = tfs
        counter += 1
        if counter % 10000 == 0:
            print counter
    print "Done"
    return termFreq

def generateFeatures(queryTermsDict, termFreq, titleTermFreq, outFile):
    out = open(outFile, "w")
    for qid, queryTerms in queryTermsDict.items():
        print "Query %d" % qid
        counter = 0
        for did, tfs in termFreq.items():
            features = getFeaturesQueryDoc(did, queryTerms, tfs)
            titleFeatures = getFeaturesQueryDoc(did, queryTerms, titleTermFreq[did])
            out.write("%d %d " % (qid, did))
            out.write(" ".join(map(str, features + titleFeatures)))
            out.write("\n")
            counter += 1
            if counter % 10000 == 0:
                print "Done %d docs" % counter
    out.close()

#writeCollectionStats(STATS_FILE)
#writeDocTermsDict(DOC_IDS_FILE, DOCS_DIR, DOC_TERMS_FILE)
#writeDocTitleTermsDict(DOC_IDS_FILE, DOCS_DIR, DOC_TITLE_TERMS_FILE)
#writeQueryTermDict(QUERIES_2014, QUERIES_2014_TERMS_FILE)
#writeQueryTermDict(QUERIES_2015, QUERIES_2015_TERMS_FILE)

docFreq, numDocs, avgDocLen = readCollectionStats(STATS_FILE)
queryTermsDict2014 = getQueryTermsDict(QUERIES_2014)
queryTermsDict2015 = getQueryTermsDict(QUERIES_2015)
termFreq = readTermFreq(DOC_TERMS_FILE)
titleTermFreq = readTermFreq(DOC_TITLE_TERMS_FILE)

generateFeatures(queryTermsDict2014, termFreq, titleTermFreq, FEATURES_2014)
generateFeatures(queryTermsDict2015, termFreq, titleTermFreq, FEATURES_2015)

def topScores(ifile, outfile):
    scores = {}
    for line in open(ifile):
        parts = line.split()
        qid = int(parts[0])
        did = int(parts[1])
        score = float(parts[2])
        if qid in scores:
            scores[qid].append((did, score))
        else:
            scores[qid] = [(did, score)]
    ordered = {}
    for qid, docscores in scores.items():
        ordered[qid] = sorted(docscores, key=lambda x:x[1], reverse=True)
        
    out = open(outfile, "w")
    for qid, docscores in ordered.items():
        rank = 1
        for did, score in docscores[:100]:
            out.write("%d Q0 %d %d %f STANDARD\n" % (qid, did, rank, score))
            rank += 1
    out.close

#topScores(FEATURES_2014, "results2014.txt")        
#topScores(FEATURES_2015, "results2015-A.txt")
        
        
        

