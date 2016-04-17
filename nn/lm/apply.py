#!/bin/python

class_id = "diag"
baseline_res_file = "../../data/results-2015-A-" + class_id + ".txt"

rerankings = []
for line in open("rankings.txt"):
    rankings = map(int, line.split())
    rerankings.append(rankings)

baseline_res = open(baseline_res_file).readlines()
baseline_res = [baseline_res[i:i+100] for i in range(0, len(baseline_res), 100)]

assert(len(baseline_res) == 10)

reranked = []
for rankings, res in zip(rerankings,baseline_res):
    reranked.append([res[i] for i in rankings])

out = open(baseline_res_file + ".reranked.lm", "w")
for res in reranked:
    rank = 1
    score = 100
    for line in res:
        parts = line.split()
        out.write("%s %s %s %g %g STANDARD\n" % (parts[0], parts[1], parts[2], rank, score))
        rank += 1
        score -= 1
        
out.close()
