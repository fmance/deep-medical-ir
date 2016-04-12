#!/bin/python

import os, time, codecs, gensim, time
from shutil import copyfile
import numpy as np
#import matplotlib.pyplot as plt


EMBED_SIZE = 100
MAX_DOC_LEN = 500

QRELS_2014 = "../../data/qrels2014.txt"
TRAIN_DIR = "../../data/training/docs/"
LABELS_TRAIN = "../../data/training/labels.txt"
DOCS_TRAIN = "../../data/training/docs.txt"

QRELS_2015 = "../../data/qrels-treceval-2015.txt"
TEST_DIR = "../../data/test/docs/"
LABELS_TEST = "../../data/test/labels.txt"
DOCS_TEST = "../../data/test/docs.txt"

ALL_TEST_DIR = "../../data/test-all/docs"
ALL_TEST_DOCS = "../../data/test-all/docs.txt"
ALL_TEST_LABELS = "../../data/test-all/labels.txt.labelled"

LABELLED_DOCS_DIR = "../../data/labelled-docs/"





def write_all_tests_set():
    vocab_map = read_vocabulary_mapping()
    print "read vocab map"
    
    docs = get_results_docs()

    doc_ids = sorted(docs)
    label_file_labelled = open(ALL_TEST_LABELS, "w")
    for doc_id in doc_ids:
        label_file_labelled.write(doc_id + "\n")
    label_file_labelled.close()
    print doc_ids

    doc_file = codecs.open(ALL_TEST_DOCS, "w", "utf-8")
    for doc_id in doc_ids:
        words = codecs.open(os.path.join(ALL_TEST_DIR, doc_id + ".txt.sent"), "r", "utf-8").read().split()
#        #truncate/pad
        words = words[0:MAX_DOC_LEN]
        word_ids = [vocab_map[w] for w in words]
        pad_id = vocab_map["<PAD>"]
        word_ids += [pad_id] * (MAX_DOC_LEN - len(words))
        for wid in word_ids:
            doc_file.write(str(wid) + " ")
#        for word in words:
#            doc_file.write(word)
#            doc_file.write(" ")
        doc_file.write("\n")
        
        
    doc_file.close()

#write_all_tests_set()



def doc_len_hist():
    labels = get_doc_labels(QRELS_2014)
    lengths = []
    for doc_id in labels.keys():
        l = len(open(os.path.join(TRAIN_DIR, doc_id + ".txt.sent")).read().split())
        lengths.append(l)
    return lengths

#hist = doc_len_hist()
#plt.hist(hist, bins=range(0, 1000, 10))
#plt.show()



