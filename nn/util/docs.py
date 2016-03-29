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

def write_vocabulary_mapping():
    count = 0
    start = time.time()
    vocab = set(["<PAD>"])
    for sdir in [os.path.join("../../data/sentences/", d) for d in ["00", "01", "02", "03"]]:
        for ssdir in [os.path.join(sdir, ssdir) for ssdir in sorted(os.listdir(sdir))]:
            for fname in [os.path.join(ssdir, fname) for fname in sorted(os.listdir(ssdir))]:
                count += 1
                if count % 10000 == 0:
                    print "%d files #words: %d (%s) in %.2f minutes" % (count, len(vocab), ssdir, (time.time() - start)/60.0)
                words = codecs.open(fname, "r", "utf-8").read().split()
                doc_len = len(words)
                vocab.update(words)
    print "---------------"
    print "Vocab size: %d" % (len(vocab))
    vocmap = codecs.open("../vocmap.txt", "w", "utf-8")
    for index, word in enumerate(vocab):
        vocmap.write(word + " " + str(index) + "\n")
    vocmap.close()

#write_vocabulary_mapping()

def read_vocabulary_mapping():
    vocmap = {}
    for line in codecs.open("../vocmap.txt", "r", "utf-8"):
        s = line.split()
        vocmap[s[0]] = int(s[1])
    return vocmap

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

#def get_test_doc_labels():
#    test_labels = get_doc_labels(QRELS_2015)
#    train_labels = get_doc_labels(QRELS_2014)
#    #remove the ones that are also training docs
#    return {doc: test_labels[doc] for doc in test_labels if doc not in train_labels}

def locate_docs(doc_ids):
    doc_names = {doc_id + ".txt.sent" : doc_id for doc_id in doc_ids}
    paths = {}
    for root, dirs, files in os.walk("../../data/sentences"):
        for doc_name in doc_names.keys():
            if doc_name in files:
                paths[doc_names[doc_name]] = os.path.join(root, doc_name)
    return paths

def get_labelled_docs():
    docs = {}
    docs.update(get_doc_labels(QRELS_2014))
    docs.update(get_doc_labels(QRELS_2015))
    return docs

def copy_labelled_docs():
    docs = get_labelled_docs()
    print str(len(docs)) + " labelled docs"
    paths = locate_docs(docs.keys())
    for doc_id, path in paths.items():
        copyfile(path, os.path.join(LABELLED_DOCS_DIR, os.path.basename(path)))

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
    return res2014 | res2015A | res2015B

def get_training_and_test_docs():
    res = get_results_docs()
    labelled_docs = get_labelled_docs()

    test_doc_ids = set(labelled_docs.keys()) & res
    test_docs = {doc_id : labelled_docs[doc_id] for doc_id in test_doc_ids}
    
    train_doc_ids = set(labelled_docs.keys()) - res
    train_docs = {doc_id : labelled_docs[doc_id] for doc_id in train_doc_ids}

    return train_docs, test_docs

def copy_all_results_docs():
    docs = get_results_docs()
    print str(len(docs)) + " result docs"
    paths = locate_docs(docs)
    for doc_id, path in paths.items():
        copyfile(path, os.path.join(ALL_TEST_DIR, os.path.basename(path)))

#copy_all_results_docs()

#def copy_training_docs():
#    labels = get_doc_labels(QRELS_2014)
#    paths = locate_docs(labels.keys())
#    print "found locations " + str(len(paths))
#    for doc_id, path in paths.items():
#        copyfile(path, os.path.join(TRAIN_DIR, os.path.basename(path)))

#def copy_test_docs():
#    labels = get_test_doc_labels()
#    paths = locate_docs(labels.keys())
#    print "found locations " + str(len(paths))
#    for doc_id, path in paths.items():
#        copyfile(path, os.path.join(TEST_DIR, os.path.basename(path)))

#copy_training_docs()
#copy_test_docs()

def write_doc_mapping(vocab_map, labels, label_file, docs_file):
    doc_ids = sorted(labels.keys())
    label_filep = open(label_file, "w")
    label_file_labelled = open(label_file + ".labelled", "w")
    for doc_id in doc_ids:
        l = labels[doc_id]
        label_filep.write(str(l[0]) + " " + str(l[1]) + " " + str(l[2]) + "\n")
        label_file_labelled.write(doc_id + " ")
        label_file_labelled.write(str(l[0]) + " " + str(l[1]) + " " + str(l[2]) + "\n")
    label_filep.close()
    label_file_labelled.close()
    print doc_ids

    doc_file = open(docs_file, "w")
    for doc_id in doc_ids:
        words = codecs.open(os.path.join(LABELLED_DOCS_DIR, doc_id + ".txt.sent"), "r", "utf-8").read().split()
        #truncate/pad
        words = words[0:MAX_DOC_LEN]
        word_ids = [vocab_map[w] for w in words]
        pad_id = vocab_map["<PAD>"]
        word_ids += [pad_id] * (MAX_DOC_LEN - len(words))
        for wid in word_ids:
            doc_file.write(str(wid) + " ")
        doc_file.write("\n")
    doc_file.close()

def write_train_and_test_sets():
    vocab_map = read_vocabulary_mapping()
    print "read vocab map"

    train_docs, test_docs = get_training_and_test_docs()

    print "writing training set"
    write_doc_mapping(vocab_map, train_docs, LABELS_TRAIN, DOCS_TRAIN)

    print "writing test set"
    write_doc_mapping(vocab_map, test_docs, LABELS_TEST, DOCS_TEST)

#write_train_and_test_sets()

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

    doc_file = open(ALL_TEST_DOCS, "w")
    for doc_id in doc_ids:
        words = codecs.open(os.path.join(ALL_TEST_DIR, doc_id + ".txt.sent"), "r", "utf-8").read().split()
        #truncate/pad
        words = words[0:MAX_DOC_LEN]
        word_ids = [vocab_map[w] for w in words]
        pad_id = vocab_map["<PAD>"]
        word_ids += [pad_id] * (MAX_DOC_LEN - len(words))
        for wid in word_ids:
            doc_file.write(str(wid) + " ")
        doc_file.write("\n")
    doc_file.close()

write_all_tests_set()

# !! also account for <PAD>
# the w2v floats are truncated to 6 digits
def write_embeddings():
    vocab_map = read_vocabulary_mapping()
    print "Read mapping"
    inv_map = {index:word for word,index in vocab_map.items()}
    sorted_indexes = range(0, len(vocab_map))
    print "reading w2v"
    model = gensim.models.Word2Vec.load("../w2v/model")
    print "read w2v"
    embeddings = open("../../data/training/w2v.txt", "w")

    counter = 0
    for index in sorted_indexes:
        emb = [0.0] * EMBED_SIZE
        word = inv_map[index]
        if word in model:
            emb = model[word]
        else:
            print "\n\nWARNING: " + word + " not in w2v model\n\n"
        embeddings.write(" ".join(str(x) for x in emb))
        embeddings.write("\n")

        counter += 1
        if (counter % 100000 == 0):
            print counter
    embeddings.close()

#write_embeddings()

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



