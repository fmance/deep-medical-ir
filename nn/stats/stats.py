#!/bin/python

import codecs, os
from collections import defaultdict, Counter
import time
import regex, math

STATS_FILE = "stats.txt"
QUERIES_2014 = "../../data/topics-2014.xml.plaintext"
QUERIES_2015 = "../../data/topics-2015-A.xml.plaintext"
DOCS_DIR = "../../data/nn/qrel-and-res-docs/"
DOC_IDS_FILE = DOCS_DIR + "ids.txt"
DOC_TERMS_FILE = "doc-terms.txt"

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

# From Lucene 5.5 https://lucene.apache.org/core/5_5_0/core/org/apache/lucene/search/similarities/BM25Similarity.html
def bm25(qterms, docTermCounter, docLen):
    score = 0.0
    k = 1.2
    b = 0.75
    for qterm in qterms:
        tf = docTermCounter[qterm]
        df = docFreq[qterm]
        idf = math.log(1 + (numDocs - df + 0.5)/(df + 0.5))
        norm = k * (1.0 - b + b * float(docLen)/avgDocLen)
        score += idf * tf * (k+1) / (tf + norm)
    return score

# From Lucene 5.5 https://lucene.apache.org/core/5_5_0/core/org/apache/lucene/search/similarities/TFIDFSimilarity.html
def tfidf(qterms, docTermCounter, docLen):
    score = 0.0
    ssw = 0.0
    matches = 0.0
    for qterm in qterms:
        tf = docTermCounter[qterm]
        df = docFreq[qterm]
        idf = 1 + math.log(float(numDocs)/(df + 1))
        idf2 = idf * idf
        ssw += idf2
        matches += int(tf > 0)
        score += math.sqrt(tf) * idf2
    coord = matches/len(qterms)
    queryNorm = 1.0/math.sqrt(ssw)
    docNorm = 1.0/math.sqrt(1 + docLen)
    return coord * queryNorm * score * docNorm

def getFeaturesQueryDoc(did, qterms, docterms):
    docTermCounter = Counter(docterms)
    docLen = len(docterms)
    return [bm25(qterms, docTermCounter, docLen), tfidf(qterms, docTermCounter, docLen)]

def getFeaturesQueryAllDocs(qid, queryTerms, docTermsDict):
    print "Getting features for query id %d" % qid
    return {did: getFeaturesQueryDoc(did, queryTerms, docTerms) for did, docTerms in docTermsDict.items()}

def getFeaturesAllQueriesAllDocs(queryTermsDict, docTermsDict):
    return {qid: getFeaturesQueryAllDocs(qid, queryTerms, docTermsDict) for qid, queryTerms in queryTermsDict.items()}

def getQueryTermsDict(queryFile):
    queries = {}
    for line in codecs.open(queryFile, "r", "utf-8"):
        parts = line.split()
        qid = int(parts[0])
        qtext = " ".join(parts[1:])
        qterms = filterTerms(stripAndLower(qtext).split())
        queries[qid] = qterms
    return queries

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

def readDocTermsDict(filename):
    docTermsDict = {}
    for line in codecs.open(filename, "r", "utf-8"):
        parts = line.split()
        docTermsDict[int(parts[0])] = parts[1:]
    return docTermsDict
    
def generateFeatures(queryTermsDict, docTermsDict, outFile):
    features = getFeaturesAllQueriesAllDocs(queryTermsDict, docTermsDict)
    out = open(outFile, "w")
    for qid, featuresQueryAllDocs in features.items():
        for did, featuresQueryDoc in featuresQueryAllDocs.items():
            out.write("%d %d " % (qid, did))
            out.write(" ".join(map(str, featuresQueryDoc)))
            out.write("\n")
    out.close()

#writeCollectionStats(STATS_FILE)
#writeDocTermsDict(DOC_IDS_FILE, DOCS_DIR, DOC_TERMS_FILE)

docFreq, numDocs, avgDocLen = readCollectionStats(STATS_FILE)

print "Reading docs and queries"
docTermsDict = readDocTermsDict(DOC_TERMS_FILE)
queryTermsDict2014 = getQueryTermsDict(QUERIES_2014)
queryTermsDict2015 = getQueryTermsDict(QUERIES_2015)
print "Done"

generateFeatures(queryTermsDict2014, docTermsDict, "topics-2014-features.txt")
generateFeatures(queryTermsDict2015, docTermsDict, "topics-2015-features.txt")
