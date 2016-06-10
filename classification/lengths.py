#!/bin/python

import os, sys
from collections import Counter
import codecs
import pprint
import numpy

WORDS_FILE = sys.argv[1]

lines = codecs.open(WORDS_FILE, "r", "utf-8").read().splitlines()

#labels = map(int, open(sys.argv[2]).readlines())
#lines = [lines[i] for i in range(0,len(lines)) if labels[i] > 0 ]

def wordCount(text):
	words = text.split()
#	return len([w for w in words if len(w) < 15])
	return len(words)

lengths = sorted(map(lambda line: len(line.split()), lines), reverse=True)
maxLen = max(lengths)

print numpy.histogram(lengths, bins=list(numpy.arange(1000,min(maxLen, 11000),1000)) + [maxLen+1])
