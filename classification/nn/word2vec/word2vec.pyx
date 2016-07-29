#!/bin/python

import gensim
import codecs
import os
import time
import logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class Sentences(object):
	def __init__(self, dirname):
		self.dirname = dirname

	def __iter__(self):
		count = 0
		start = time.time()
		for sdir in [self.dirname + d for d in ["00", "01", "02", "03"]]:
			for ssdir in [os.path.join(sdir, ssdir) for ssdir in sorted(os.listdir(sdir))]:
				for fname in [os.path.join(ssdir, fname) for fname in sorted(os.listdir(ssdir))]:
					count += 1
					if count % 10000 == 0:
						print "\n\n%d files (%s) in %.2f minutes\n\n" % (count, ssdir, (time.time() - start)/60.0)
					for sentence in codecs.open(fname, "r", "utf-8"):
						yield sentence.split()

def run():
	sentences = Sentences("../../../data/analyzed/")
	model = gensim.models.Word2Vec(sentences, workers=4, iter=5, size=100, min_count=1)
	model.save("model")


