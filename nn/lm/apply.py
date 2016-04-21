#!/bin/python

from collections import defaultdict
import pprint

baseline_res_file = "../../data/results-2015-A.txt"
DOC_IDS_FILE = "results-2015-features.txt.ids"
QUERY_OFFSET = 100

rerankings = []
for line in open("rankings.txt"):
    rankings = map(int, line.split())
    rerankings.append(rankings)
    
docIds = defaultdict(list)
for line in open(DOC_IDS_FILE):
    parts = line.split()
    qid = int(parts[0])
    did = int(parts[1])
    docIds[qid - QUERY_OFFSET].append(did)
    
rankings = {}
for qid in range(1,31):
    dids = docIds[qid]
    rankings[qid] = [dids[i] for i in rerankings[qid-1]]

rankings = sorted(rankings.items(), key=lambda kv:kv[0])

out = open(baseline_res_file + ".reranked.lm", "w")
for qid, dids in rankings:
    rank = 1
    score = 100
    for did in dids:
        out.write("%d Q0 %d %d %f STANDARD\n" % (qid, did, rank, score))
        rank += 1
        score -= 1
        
out.close()
