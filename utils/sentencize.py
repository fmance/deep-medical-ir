#!/usr/bin/python

import nltk.data
import os
import sys
import codecs
import time
import regex

#MAX_DOC_LEN = 1000

sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

def stripAndLower(s):
	return regex.sub(ur"\P{Latin}", " ", s).lower()

def getSentences(text):
	sent = sent_detector.tokenize(text.strip(), realign_boundaries=True)
	return map(lambda s: stripAndLower(s), sent)

def sentencize(subdir):
	count = 0
	start = time.time()
	sent_dir = "../classification/data/sentences/"
	for sdir in ["../data/plaintext/" + d for d in [subdir]]:
		sent_sdir = os.path.join(sent_dir, os.path.basename(sdir))
		os.mkdir(sent_sdir)
		for ssdir in [os.path.join(sdir, ssdir) for ssdir in sorted(os.listdir(sdir))]:
			sent_ssdir = os.path.join(sent_sdir, os.path.basename(ssdir))
			os.mkdir(sent_ssdir)
			for fname in [os.path.join(ssdir, fname) for fname in sorted(os.listdir(ssdir))]:
				count += 1
				if count % 1000 == 0:
					print "Sentencized %d files (%s), took %.2f minutes" % (count, ssdir, (time.time() - start)/60.0)
				fp = codecs.open(fname, "r", "utf-8")
				out = codecs.open(os.path.join(sent_ssdir, os.path.basename(fname) + ".sent"), "w", "utf-8")
				content = fp.readlines()
				
				sentences = []
				
				for sentence in getSentences(content[0]):
					out.write("%s\n" % sentence)
				for sentence in getSentences("".join(content[1:])):
					out.write("%s\n" % sentence)
				
#				for sentence in getSentences(content[0]):
#					sentences.append(sentence)
#				for sentence in getSentences("".join(content[1:])):
#					sentences.append(sentence)
#				nw = 0
#				i = 0
#				while nw < MAX_DOC_LEN and i < len(sentences):
#					sentence = sentences[i]
#					out.write(sentence)
#					out.write("\n")
#					nw += len(sentence.split())
#					i += 1
#				
#				padding = ["<PAD>"] * (MAX_DOC_LEN - nw)
#				out.write(" ".join(padding))
				out.write("\n")

				fp.close()
				out.close()

sentencize(sys.argv[1])
