#!/bin/python

import os, time

THIS_DIR = os.path.dirname(__file__)

def writeVocabularyMap():
    count = 0
    start = time.time()
    vocab = set([])
    for sdir in [os.path.join("../../classification/data/sentences", d) for d in ["00", "01", "02", "03"]]:
        for ssdir in [os.path.join(sdir, ssdir) for ssdir in sorted(os.listdir(sdir))]:
            for fname in [os.path.join(ssdir, fname) for fname in sorted(os.listdir(ssdir))]:
                count += 1
                if count % 10000 == 0:
                    print "%d files #words: %d (%s) in %.2f minutes" % (count, len(vocab), ssdir, (time.time() - start)/60.0)
                words = open(fname, "r", encoding="utf-8").read().split()
                vocab.update(words)
    print "Vocabulary size: %d" % len(vocab)
    out = codecs.open(os.path.join(THIS_DIR, "vocmap.txt"), "w", "utf-8")
    # !!! Start from 1, reserve 0 for padding !!!
    for index, word in enumerate(vocab, 1):
    	out.write("%s %d\n" % (word, index))
    out.close()
    
writeVocabularyMap()
