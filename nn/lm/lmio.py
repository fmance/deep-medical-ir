#!/bin/python

import itertools
import random

class_id = "diag"
INPUT_TRAIN = "../../data/qrels-treceval-2014.txt"
INPUT_TEST = "../../data/results-2015-A-" + class_id + ".txt"
LM_TRAIN_FILE = "lm-" + class_id + "-train.txt"
LM_TEST_FILE = "lm-" + class_id + "-test.txt"

def get_valid_doc_ids():
    id_rows = open("../../data/valid-doc-ids.txt").read().split()
    return set(map(lambda did: int(did), id_rows))

def read_qrels(qrel_file):
    qrels = {}
    valid_dids = get_valid_doc_ids()
    for qrel in open(qrel_file):
        parts = qrel.split()
        tid = int(parts[0])
        did = int(parts[2])
        rel = int(parts[3])
        if did in valid_dids and tid <= 10:
            if (tid in qrels):
                qrels[tid].append((did, rel))
            else:
                qrels[tid] = [(did, rel)]
    return qrels

def read_features(feature_file):
    features = {}
    for line in open(feature_file):
        parts = line.split()
        tid = int(parts[0])
        did = int(parts[1])
        feats = parts[2:]
#        for x in range(0,30):
#            feats += [random.uniform(0,x)]
        features[(tid, did)] = map(float, feats)
    return features

def get_lm_target(relevance):
    if relevance > 0:
        return 1
    else:
        return -1

def get_qrel_features(qrel_file, feature_file):
    qrels = read_qrels(qrel_file)
    features = read_features(feature_file)
    qrel_feats = {}
    for tid, docrels in qrels.items():
        qrel_feats[tid] = {did: ([rel] + features[(tid, did)]) for did, rel in docrels}
    return qrel_feats

def write_input(qrel_file, feature_file, input_file):
    out = open(input_file, "w")
    for tid, docfeats in get_qrel_features(qrel_file, feature_file).items():
        for doc, feats in docfeats.items():
            out.write("%d qid:%d " % (feats[0], tid))
            numbered_feats = map(lambda (fid, fv): str(fid)+":"+str(fv), enumerate(feats[1:], 1))
            out.write(" ".join(numbered_feats))
            out.write("\n")
    out.close()   


write_input(INPUT_TRAIN, "../stats/qrels2014-feats.txt", LM_TRAIN_FILE)
write_input(INPUT_TEST, "../stats/res2015-A-feats.txt", LM_TEST_FILE)
