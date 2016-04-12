#!/bin/python

import os, codecs
from shutil import copyfile
import random
from collections import Counter

MAX_DOC_LEN = 1000

class_id = "treat"
class_dir = "../../data/nn/" + class_id + "/"
ids_file = class_dir + class_id + ".txt"

def get_docs_from_res_file(res_file):
    docs = set([])
    for line in open(res_file):
        parts = line.split()
        doc_id = int(parts[2])
        rank = int(parts[3])
        docs.update([doc_id])
    return docs

def get_results_docs():
    res2014 = get_docs_from_res_file("../../data/results-2014.txt")
    res2015A = get_docs_from_res_file("../../data/results-2015-A.txt")
    res2015B = get_docs_from_res_file("../../data/results-2015-B.txt")
    return res2014 | res2015A | res2015B

def get_valid_doc_ids():
    id_rows = open("../../data/valid-doc-ids.txt").read().split()
    return set(map(lambda did: int(did), id_rows))

def get_all_ids():
    ids = []
    for root, dirs, files in os.walk("../../data/sentences"):
        ids += map(lambda fname: int(fname.split(".")[0]), files)
    return set(ids) & get_valid_doc_ids()

def get_ids_from_file(f):
    return set(map(lambda pmc: int(pmc[3:]), open(f).readlines()))

def get_doc_labels(qrel_file):
    diag = set([])
    test = set([])
    treat = set([])
    valid_doc_ids = set(open("../../data/valid-doc-ids.txt").read().split())
    for line in open(qrel_file):
        qrel = line.split()
        topic = int(qrel[0])
        doc_id = int(qrel[2])
        relevance = int(qrel[3])
        if topic <= 10:
            if relevance > 0 and str(doc_id) in valid_doc_ids:
                diag.update([doc_id])
        elif topic <= 20:
            if relevance > 0 and str(doc_id) in valid_doc_ids:
                test.update([doc_id])
        else:
            if relevance > 0 and str(doc_id) in valid_doc_ids:
                treat.update([doc_id])
    rel_docs = set([])
    rel_docs.update(diag)
    rel_docs.update(test)
    rel_docs.update(treat)
    labels = {}
    for doc in rel_docs:
        labels[doc] = [int(doc in diag), int(doc in test), int(doc in treat)]
    return labels

def get_docs_in_qrel_file(qrel_file):
    docs = set([])
    valid_doc_ids = set(open("../../data/valid-doc-ids.txt").read().split())
    for line in open(qrel_file):
        qrel = line.split()
        topic = int(qrel[0])
        doc_id = int(qrel[2])
        relevance = int(qrel[3])
        if str(doc_id) in valid_doc_ids:
            docs.update([doc_id])
    return docs

def get_labeled_docs():
    docs = {}
    docs.update(get_doc_labels("../../data/qrels-treceval-2014.txt"))
    docs.update(get_doc_labels("../../data/qrels-treceval-2015.txt"))
    return docs
    
def get_qrel_docs():
    docs = set([])
    docs.update(get_docs_in_qrel_file("../../data/qrels-treceval-2014.txt"))
    docs.update(get_docs_in_qrel_file("../../data/qrels-treceval-2015.txt"))
    return docs  

def get_longer_docs(doc_ids):
    doc_names = {str(doc_id) + ".txt.sent" : doc_id for doc_id in doc_ids}
    doc_filenames = doc_names.keys()
    long_docs = set([])
    for root, dirs, files in os.walk("../../data/sentences"):
        print root
        matches = set(files) & set(doc_filenames)
        for m in matches:
            words = open(os.path.join(root, m)).read().split()
            if len(words) > 500:
                long_docs.update([doc_names[m]])
    return long_docs

def write_working_doc_ids_to_file():
    ids = get_all_ids()
    ids = ids - get_qrel_docs()
    ids = ids - get_results_docs()
    ids = get_longer_docs(ids)
    out = open("ids.txt", "w")
    for did in ids:
        out.write("%d\n" % did)
    out.close()

#write_working_doc_ids_to_file()

def read_working_doc_ids():
    return set(map(lambda did: int(did), open("ids.txt").readlines()))

ids = read_working_doc_ids()
pos = get_ids_from_file(ids_file) & ids
neg = ids - pos
pos = list(pos)
neg = list(neg)
random.shuffle(pos)
random.shuffle(neg)

avail_size = min(len(pos), len(neg))
train_size = int(0.8 * avail_size)
test_size = avail_size - train_size

pos_train = pos[:train_size]
pos_test = pos[train_size : train_size+test_size]
neg_train = neg[:train_size]
neg_test = neg[train_size : train_size+test_size]

train_doc_ids = pos_train + neg_train
#train_doc_ids = map(lambda did: int(did), open(class_dir + "/???/ids.txt").read().split())
train_labels = [1] * train_size + [0] * train_size
test_doc_ids = pos_test + neg_test
#test_doc_ids = map(lambda did: int(did), open(class_dir + "/???/ids.txt").read().split())
test_labels = [1] * test_size + [0] * test_size

result_doc_ids = list(get_results_docs())
all_docs = set(train_doc_ids) | set(test_doc_ids) | set(result_doc_ids)
    
def locate_docs(doc_ids):
    doc_names = {str(doc_id) + ".txt.sent" : doc_id for doc_id in doc_ids}
    doc_filenames = doc_names.keys()
    paths = {}
    counter = 0
    for root, dirs, files in os.walk("../../data/sentences"):
        counter += 1
        matches = set(files) & set(doc_filenames)
        for m in matches:
            paths[doc_names[m]] = os.path.join(root, m)
    return paths

def copy_docs(ids, directory):
    paths = locate_docs(ids)
    print "located %d/%d paths" % (len(paths), len(ids))
    counter = 0
    for doc_id, path in paths.items():
        copyfile(path, os.path.join(directory, os.path.basename(path)))
        counter += 1
        if counter % 1000 == 0:
            print counter

def write_labels(labels, filename):
    print "Writing labels to " + filename
    f = open(filename, "w")
    for label in labels:
        if (label == 1):
            f.write("1 0\n")
        else:
            f.write("0 1\n")            
    f.close()

def write_doc_mapping(vocab_map, doc_ids, filename):
    print "Writing doc mappings to " + filename

    f = open(filename, "w")

    for doc_id in doc_ids:
        words = codecs.open(os.path.join(class_dir, "labeled/", str(doc_id) + ".txt.sent"), "r", "utf-8").read().split()
        #truncate/pad
        words = words[0:MAX_DOC_LEN]
        word_ids = [vocab_map[w] for w in words]
        pad_id = vocab_map["<PAD>"]
        word_ids += [pad_id] * (MAX_DOC_LEN - len(words))
        for wid in word_ids:
            f.write("%d " % (wid))
        f.write("\n")

    f.close()

def write_doc_ids(doc_ids, filename):
    print "Writing doc ids to " + filename
    f = open(filename, "w")
    for doc_id in doc_ids:
        f.write("%d\n" % doc_id)
    f.close()

def duplicate_docs():
    texts = {}
    for doc_id in all_docs:
        texts[doc_id] = codecs.open(os.path.join(class_dir, "labeled/", str(doc_id) + ".txt.sent"), "r", "utf-8").read()
    rev = {}
    for did, text in texts.items():
        rev.setdefault(text, set()).add(did)
    all_dupl = [values for did, values in rev.items() if len(values) > 1]    
    for dupl in all_dupl:
        print len(set(train_doc_ids) & dupl)
        print len(set(test_doc_ids) & dupl)
        print len(set(test_qrels_doc_ids) & dupl)
        print "-------------------------"

def read_vocabulary_mapping():
    vocmap = {}
    for line in codecs.open("../vocmap.txt", "r", "utf-8"):
        s = line.split()
        vocmap[s[0]] = int(s[1])
    return vocmap

def write_datasets():
    vocab_map = read_vocabulary_mapping()

    print "Writing training set"
    write_labels(train_labels, class_dir + "train/labels.txt")
    write_doc_mapping(vocab_map, train_doc_ids, class_dir + "train/docs.txt")
    write_doc_ids(train_doc_ids, class_dir + "train/ids.txt")

    print "Writing test set"
    write_labels(test_labels, class_dir + "test/labels.txt")
    write_doc_mapping(vocab_map, test_doc_ids, class_dir + "test/docs.txt")
    write_doc_ids(test_doc_ids, class_dir + "test/ids.txt")

    print "Writing result set"
    write_doc_ids(result_doc_ids, class_dir + "res/ids.txt")
    write_doc_mapping(vocab_map, result_doc_ids, class_dir + "res/docs.txt")

copy_docs(all_docs, class_dir + "labeled/")
write_datasets()
