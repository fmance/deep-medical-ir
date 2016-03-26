#!/bin/python

import os, time, codecs, gensim, time
from shutil import copyfile
import numpy as np

EMBED_SIZE = 52

QRELS_2014 = "../../data/qrels2014.txt"
TRAIN_DIR = "../../data/training/docs/"
LABELS_TRAIN = "../../data/training/labels.txt"
DOCS_TRAIN = "../../data/training/docs.txt"

QRELS_2015 = "../../data/qrels-treceval-2015.txt"
TEST_DIR = "../../data/test/docs/"
LABELS_TEST = "../../data/test/labels.txt"
DOCS_TEST = "../../data/test/docs.txt"

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

def read_vocabulary_mapping():
    vocmap = {}
    for line in codecs.open("../vocmap.txt", "r", "utf-8"):
        s = line.split()
        vocmap[s[0]] = int(s[1])
    return vocmap

def get_docs(qrel_file):
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

def locate_docs(doc_ids):
    doc_names = {doc_id + ".txt.sent" : doc_id for doc_id in doc_ids}
    paths = {}
    for root, dirs, files in os.walk("../../data/sentences"):
        for doc_name in doc_names.keys():
            if doc_name in files:
                paths[doc_names[doc_name]] = os.path.join(root, doc_name)
    return paths

def copy_docs(qrel_file, dest_dir):
    labels = get_docs(qrel_file)
    paths = locate_docs(labels.keys())
    print "found locations " + str(len(paths))
    for doc_id, path in paths.items():
        copyfile(path, os.path.join(dest_dir, os.path.basename(path)))

def write_data(qrel_file, label_file, docs_file, docs_dir):
    labels = get_docs(qrel_file)
    vocab_map = read_vocabulary_mapping()

    doc_ids = sorted(labels.keys())
    label_file = open(label_file, "w")
    for doc_id in doc_ids:
        l = labels[doc_id]
        label_file.write(str(l[0]) + " " + str(l[1]) + " " + str(l[2]) + "\n")
    label_file.close()
    print doc_ids

    doc_file = open(docs_file, "w")
    for doc_id in doc_ids:
        words = codecs.open(os.path.join(docs_dir, doc_id + ".txt.sent"), "r", "utf-8").read().split()
        #truncate/pad to 50,000 words
        words = words[0:50000]
        word_ids = [vocab_map[w] for w in words]
        padmap = vocab_map["<PAD>"]
        word_ids += [padmap] * (50000 - len(words))
        for wid in word_ids:
            doc_file.write(str(wid) + " ")
        doc_file.write("\n")
    doc_file.close()

write_data(QRELS_2015, LABELS_TEST, DOCS_TEST, TEST_DIR)

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
        embeddings.write(" ".join(str(x) for x in emb))
        embeddings.write("\n")
        
        counter += 1
        if (counter % 100000 == 0):
            print counter
    embeddings.close()

#write_embeddings()

