#!/bin/python

import os, time, codecs, gensim, time
from shutil import copyfile
import numpy as np
#import matplotlib.pyplot as plt

MAX_DOC_LEN = 1000
EMBED_SIZE = 100

def get_doc_labels(qrel_file):
    diag = set([])
    test = set([])
    treat = set([])
    valid_doc_ids = set(open("../../data/valid-doc-ids.txt").read().split())
    for line in open(qrel_file):
        qrel = line.split()
        topic = int(qrel[0])
        doc_id = qrel[2]
        relevance = int(qrel[3])
        if topic <= 10:
            if relevance > 0 and doc_id in valid_doc_ids:
                diag.update([doc_id])
        elif topic <= 20:
            if relevance > 0 and doc_id in valid_doc_ids:
                test.update([doc_id])
        else:
            if relevance > 0 and doc_id in valid_doc_ids:
                treat.update([doc_id])
    rel_docs = set([])
    rel_docs.update(diag)
    rel_docs.update(test)
    rel_docs.update(treat)
    labels = {}
    for doc in rel_docs:
        labels[doc] = [int(doc in diag), int(doc in test), int(doc in treat)]
    return labels

def get_labeled_docs():
    docs = {}
    docs.update(get_doc_labels("../../data/qrels-treceval-2014.txt"))
    docs.update(get_doc_labels("../../data/qrels-treceval-2015.txt"))
    return docs

def locate_docs(doc_ids):
    doc_names = {str(doc_id) + ".txt.sent" : doc_id for doc_id in doc_ids}
    paths = {}
    for root, dirs, files in os.walk("../../data/sentences"):
        for doc_name in doc_names.keys():
            if doc_name in files:
                paths[doc_names[doc_name]] = os.path.join(root, doc_name)
    return paths

def copy_labeled_docs():
    docs = get_labeled_docs()
    small = []
    print "Found " + str(len(docs)) + " labeled docs"
    paths = locate_docs(docs.keys())
    for doc_id, path in paths.items():
        copyfile(path, os.path.join("../../data/nn/labeled", os.path.basename(path)))

def get_docs_from_res_file(res_file):
    docs = set([])
    for line in open(res_file):
        parts = line.split()
        doc_id = parts[2]
        rank = int(parts[3])
        docs.update([doc_id])
    return docs

def get_results_docs():
    res2014 = get_docs_from_res_file("../../data/results-2014.txt")
    res2015A = get_docs_from_res_file("../../data/results-2015-A.txt")
    res2015B = get_docs_from_res_file("../../data/results-2015-B.txt")
    #return res2014 | res2015A | res2015B
    return res2015A

#def get_training_and_test_docs():
#    res = get_results_docs()
#    labeled_docs = get_labeled_docs()

#    test_doc_ids = set(labeled_docs.keys()) & res
#    test_docs = {doc_id : labeled_docs[doc_id] for doc_id in test_doc_ids}

#    train_doc_ids = set(labeled_docs.keys()) - res
#    train_docs = {doc_id : labeled_docs[doc_id] for doc_id in train_doc_ids}

#    return train_docs, test_docs

def get_training_and_test_docs():
    train_docs = get_doc_labels("../../data/qrels-treceval-2014.txt")
    
    test_docs = get_doc_labels("../../data/qrels-treceval-2015.txt")
    test_docs = {doc_id: test_docs[doc_id] for doc_id in test_docs if doc_id not in train_docs}

    return train_docs, test_docs

def write_labels(doc_labels, filename):
    print "Writing labels to " + filename

    f = open(filename, "w")
    f_with_doc_ids = open(filename + ".with_doc_ids", "w")

    for doc_id in sorted(doc_labels.keys()):
        label = doc_labels[doc_id]
        diag_label = [-1, -1]
        
        if (label[0] == 1):
            diag_label = [1,0]
        else:
            diag_label = [0,1]
            
        f.write("%d %d\n" % (tuple(diag_label)))
        f_with_doc_ids.write("%s %d %d\n" % (doc_id, diag_label[0], diag_label[1]))

    f.close()
    f_with_doc_ids.close()


def write_doc_mapping(vocab_map, doc_labels, filename):
    print "Writing doc mappings to " + filename

    f = open(filename, "w")

    for doc_id in sorted(doc_labels.keys()):
        words = codecs.open(os.path.join("../../data/nn/labeled/", doc_id + ".txt.sent"), "r", "utf-8").read().split()
        #truncate/pad
        words = words[0:MAX_DOC_LEN]
        word_ids = [vocab_map[w] for w in words]
        pad_id = vocab_map["<PAD>"]
        word_ids += [pad_id] * (MAX_DOC_LEN - len(words))
        for wid in word_ids:
            f.write("%d " % (wid))
        f.write("\n")

    f.close()

def read_vocabulary_mapping():
    vocmap = {}
    for line in codecs.open("../vocmap.txt", "r", "utf-8"):
        s = line.split()
        vocmap[s[0]] = int(s[1])
    return vocmap

def write_datasets():
    vocab_map = read_vocabulary_mapping()
    train_doc_labels, test_doc_labels = get_training_and_test_docs()

    print "Writing training set"
    write_labels(train_doc_labels, "../../data/nn/train/labels.txt")
    write_doc_mapping(vocab_map, train_doc_labels, "../../data/nn/train/docs.txt")

    print "Writing test set"
    write_labels(test_doc_labels, "../../data/nn/test/labels.txt")
    write_doc_mapping(vocab_map, test_doc_labels, "../../data/nn/test/docs.txt")

def copy_all_results_docs():
    docs = get_results_docs()
    print str(len(docs)) + " result docs"
    paths = locate_docs(docs)
    for doc_id, path in paths.items():
        copyfile(path, os.path.join(ALL_TEST_DIR, os.path.basename(path)))

# !! also account for <PAD>
# the w2v floats are truncated to 6 digits
def write_embeddings():
    vocab_map = read_vocabulary_mapping()
    inv_vocab_map = {index:word for word,index in vocab_map.items()}

    print "Reading w2v"
    model = gensim.models.Word2Vec.load("../w2v/model")

    embeddings = open("../embeddings.txt", "w")

    for index in range(0, len(vocab_map)):
        embedding = [0.0] * EMBED_SIZE
        word = inv_vocab_map[index]
        if word in model:
            embedding = model[word]
        else:
            print "\n\nWARNING: " + word + " not in w2v model\n\n"
        embeddings.write(" ".join(str(x) for x in embedding))
        embeddings.write("\n")

        if (index % 100000 == 0):
            print index

    embeddings.close()


def doc_len_hist():
    doc_labels = get_labeled_docs()
    lengths = []
    for doc_id in doc_labels.keys():
        l = len(open(os.path.join("../../data/nn/diag/labeled", doc_id + ".txt.sent")).read().split())
        lengths.append(l)
    plt.hist(lengths, bins=range(0, 2000, 500))
    plt.show()

#copy_labeled_docs()
#write_datasets()
write_embeddings()
