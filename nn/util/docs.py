#!/bin/python

import os, time, codecs
from shutil import copyfile


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
        vocmap[s[0]] = s[1]
    return vocmap   
    

def get_train_docs():
    diag = set([])
    test = set([])
    treat = set([])
    valid_doc_ids = set(open("../../data/valid-doc-ids.txt").read().split())
    for line in open("../../data/qrels2014.txt"):
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

def copy_training():
    labels = get_train_docs()
    paths = locate_docs(labels.keys())
    print "found locations " + str(len(paths))
    for doc_id, path in paths.items():
        copyfile(path, os.path.join("../../data/training/docs/", os.path.basename(path)))

def write_training_data():
    labels = get_train_docs()
    vocab_map = read_vocabulary_mapping()
    
    doc_ids = sorted(labels.keys())
    label_file = open("../../data/training/labels.txt", "w")
    for doc_id in doc_ids:
        l = labels[doc_id]
        label_file.write(str(l[0]) + " " + str(l[1]) + " " + str(l[2]) + "\n")
    label_file.close()
    print doc_ids
    
    # TODO padding
    doc_file = open("../../data/training/docs.txt", "w")
    for doc_id in doc_ids:
        words = codecs.open(os.path.join("../../data/training/docs/", doc_id + ".txt.sent"), "r", "utf-8").read().split()
        word_ids = [vocab_map[w] for w in words]
        for wid in word_ids:
            doc_file.write(str(wid) + " ")
        doc_file.write("\n")
    doc_file.close()

write_training_data()
