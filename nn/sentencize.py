#!/usr/bin/python

import nltk.data
import os
import codecs
import time

sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

def stripAndLower(s):
    return s.rstrip(".").lower()

def getSentences(text):
    sent = sent_detector.tokenize(text.strip(), realign_boundaries=True)
    return map(lambda s: stripAndLower(s), sent)

def sentencize():
    count = 0
    start = time.time()
    sent_dir = "../data/sentences/"
    os.mkdir(sent_dir)
    for sdir in ["../data/plaintext/" + d for d in ["00", "01", "02", "03"]]:
        sent_sdir = os.path.join(sent_dir, os.path.basename(sdir))
        os.mkdir(sent_sdir)
        for ssdir in [os.path.join(sdir, ssdir) for ssdir in sorted(os.listdir(sdir))]:
            sent_ssdir = os.path.join(sent_sdir, os.path.basename(ssdir))
            os.mkdir(sent_ssdir)
            for fname in [os.path.join(ssdir, fname) for fname in sorted(os.listdir(ssdir))]:
                count += 1
                if count % 1000 == 0:
                    print "Sentencized %d files (%s), took %02d minutes" % (count, ssdir, (time.time() - start)/60)
                fp = codecs.open(fname, "r", "utf-8")
                out = codecs.open(os.path.join(sent_ssdir, os.path.basename(fname) + ".sent"), "w", "utf-8")
                for sentence in getSentences(fp.read()):
                    out.write(sentence + "\n")
                fp.close()
                out.close()

sentencize()

#out = codecs.open("art.txt", "w", "utf-8")
#out.write("\n\n".join(getSentences(codecs.open("art0.txt", "r", "utf-8").read())))
