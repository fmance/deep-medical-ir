#!/bin/python

import os, codecs, time

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
    print "Vocabulary size: %d" % (len(vocab))
    vocmap = codecs.open("../vocmap.txt", "w", "utf-8")
    for index, word in enumerate(vocab):
        vocmap.write(word + " " + str(index) + "\n")
    vocmap.close()

def write_vocabulary_mapping_labeled_only():
    vocab = set(["<PAD>"])
    ssdir = "../../data/nn/docs/labeled/"
    for fname in [os.path.join(ssdir, fname) for fname in sorted(os.listdir(ssdir))]:
        words = codecs.open(fname, "r", "utf-8").read().split()
        vocab.update(words)
    print "Vocabulary size: %d" % (len(vocab))
    vocmap = codecs.open("../vocmap.txt", "w", "utf-8")
    for index, word in enumerate(vocab):
        vocmap.write(word + " " + str(index) + "\n")
    vocmap.close()

write_vocabulary_mapping()    
