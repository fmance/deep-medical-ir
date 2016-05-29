#!/usr/bin/python

import nltk.data
import os
import sys
import codecs
import time
import regex

def trecacize(subdir):
	count = 0
	start = time.time()
	trec_dir = "../data/plaintext-trec/"
	for sdir in ["../data/plaintext/" + d for d in [subdir]]:
		trec_sdir = os.path.join(trec_dir, os.path.basename(sdir))
		os.mkdir(trec_sdir)
		for ssdir in [os.path.join(sdir, ssdir) for ssdir in sorted(os.listdir(sdir))]:
			trec_ssdir = os.path.join(trec_sdir, os.path.basename(ssdir))
			os.mkdir(trec_ssdir)
			for fname in [os.path.join(ssdir, fname) for fname in sorted(os.listdir(ssdir))]:
				count += 1
				if count % 1000 == 0:
					print "Trecacized %d files (%s), took %.2f minutes" % (count, ssdir, (time.time() - start)/60.0)
				content = codecs.open(fname, "r", "utf-8").read()
				out = codecs.open(os.path.join(trec_ssdir, os.path.basename(fname) + ".txt"), "w", "utf-8")

				docno = int(os.path.splitext(os.path.basename(fname))[0])

				out.write("<DOC>\n")
				out.write("<DOCNO> %d </DOCNO>\n" % docno)
				out.write(content)
				out.write("\n")
				out.write("</DOC>\n")

				out.close()

trecacize(sys.argv[1])
