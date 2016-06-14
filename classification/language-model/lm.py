"""
======================================================
Classification of text documents using sparse features
======================================================

This is an example showing how scikit-learn can be used to classify documents
by topics using a bag-of-words approach. This example uses a scipy.sparse
matrix to store the features and demonstrates various classifiers that can
efficiently handle sparse matrices.

The dataset used in this example is the 20 newsgroups dataset. It will be
automatically downloaded, then cached.

The bar plot indicates the accuracy, training time (normalized) and test time
(normalized) of each classifier.

"""

# Author: Peter Prettenhofer <peter.prettenhofer@gmail.com>
#		 Olivier Grisel <olivier.grisel@ensta.org>
#		 Mathieu Blondel <mathieu@mblondel.org>
#		 Lars Buitinck <L.J.Buitinck@uva.nl>
# License: BSD 3 clause

from __future__ import print_function

import logging
import numpy as np
from optparse import OptionParser
import sys
from time import time
import codecs
import re
import os
import itertools
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_selection import SelectKBest, chi2, SelectFromModel
from sklearn.linear_model import RidgeClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import Perceptron
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, GradientBoostingClassifier, BaggingClassifier
from sklearn.utils.extmath import density
from sklearn import metrics
from sklearn.neural_network import BernoulliRBM


# Display progress logs on stdout
logging.basicConfig(level=logging.INFO,
					format='%(asctime)s %(levelname)s %(message)s')


# parse commandline arguments
op = OptionParser()
op.add_option("--report",
			  action="store_true", dest="print_report",
			  help="Print a detailed classification report.")
op.add_option("--chi2_select",
			  action="store", type="int", dest="select_chi2",
			  help="Select some number of features using a chi-squared test")
op.add_option("--confusion_matrix",
			  action="store_true", dest="print_cm",
			  help="Print the confusion matrix.")
op.add_option("--top10",
			  action="store_true", dest="print_top10",
			  help="Print ten most discriminative terms per class"
				   " for every classifier.")
op.add_option("--all_categories",
			  action="store_true", dest="all_categories",
			  help="Whether to use all categories or not.")
op.add_option("--use_hashing",
			  action="store_true",
			  help="Use a hashing vectorizer.")
op.add_option("--n_features",
			  action="store", type=int, default=2 ** 16,
			  help="n_features when using the hashing vectorizer.")
op.add_option("--filtered",
			  action="store_true",
			  help="Remove newsgroup information that is easily overfit: "
				   "headers, signatures, and quoting.")

(opts, args) = op.parse_args()
print(__doc__)
op.print_help()
print()






def clean_str(string):
	"""
	Tokenization/string cleaning for all datasets except for SST.
	Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
	"""
	string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
	string = re.sub(r"\'s", " \'s", string)
	string = re.sub(r"\'ve", " \'ve", string)
	string = re.sub(r"n\'t", " n\'t", string)
	string = re.sub(r"\'re", " \'re", string)
	string = re.sub(r"\'d", " \'d", string)
	string = re.sub(r"\'ll", " \'ll", string)
	string = re.sub(r",", " , ", string)
	string = re.sub(r"!", " ! ", string)
	string = re.sub(r"\(", " \( ", string)
	string = re.sub(r"\)", " \) ", string)
	string = re.sub(r"\?", " \? ", string)
	string = re.sub(r"\s{2,}", " ", string)
	return string.strip().lower()


def load_data_and_labels():
	"""
	Loads MR polarity data from files, splits the data into words and generates labels.
	Returns split sentences and labels.
	"""
	# Load data from files
	positive_examples = list(open("../nn/tut/cnn-text-classification-tf/data/rt-polaritydata/rt-polarity.pos", "r").readlines())
	positive_examples = [s.strip() for s in positive_examples]
	negative_examples = list(open("../nn/tut/cnn-text-classification-tf/data/rt-polaritydata/rt-polarity.neg", "r").readlines())
	negative_examples = [s.strip() for s in negative_examples]
	# Split by words
	x_text = positive_examples + negative_examples
	x_text = [clean_str(sent) for sent in x_text]
	#x_text = [s.split(" ") for s in x_text]
	# Generate labels
	positive_labels = [1 for _ in positive_examples]
	negative_labels = [0 for _ in negative_examples]
	y = np.concatenate([positive_labels, negative_labels], 0)
	return [x_text, y]






###############################################################################
# Load some categories from the training set
if opts.all_categories:
	categories = None
else:
	categories = [
		"pos", "neg"
	]

if opts.filtered:
	remove = ('headers', 'footers', 'quotes')
else:
	remove = ()

print(categories if categories else "all")

## Load data
#print("Loading data...")
#x, y = load_data_and_labels()
## Randomly shuffle data
#np.random.seed(10)
#shuffle_indices = np.random.permutation(np.arange(len(y)))
#x_shuffled = [x[i] for i in shuffle_indices]
#y_shuffled = [y[i] for i in shuffle_indices]
## Split train/test set
## TODO: This is very crude, should use cross-validation
#x_train, x_dev = x_shuffled[:-1000], x_shuffled[-1000:]
#y_train, y_dev = y_shuffled[:-1000], y_shuffled[-1000:]
#print("Train/Dev split: {:d}/{:d}".format(len(y_train), len(y_dev)))

data_train = type('', (), {})()
data_test = type('', (), {})()
data_res = type('', (), {})()
data_relevant_qrels = type('', (), {})()

#data_train.data = x_train
#data_train.target = y_train

#data_test.data = x_dev
#data_test.target = y_dev

class_id = sys.argv[1]
class_dir = "../data/" + class_id + "/"
results_dir = os.path.join("../data", "res-and-qrels", "results", class_id)

data_train.data = (codecs.open(class_dir + "train/words.txt", "r", "utf-8").read().splitlines())
data_train.target = (map(lambda x: int(x), codecs.open(class_dir + "train/labels.txt", "r", "utf-8").readlines()))

data_test.data = codecs.open(class_dir + "test/words.txt", "r", "utf-8").read().splitlines()
data_test.target = map(lambda x: int(x), codecs.open(class_dir + "test/labels.txt", "r", "utf-8").readlines())

data_res.data = codecs.open("../data/res-and-qrels/words.txt", "r", "utf-8").read().splitlines()

#data_relevant_qrels.data = codecs.open("../data/relevant-qrel-docs/words.txt", "r", "utf-8").readlines()
#data_relevant_qrels.target = map(lambda x: int(x), codecs.open("../data/relevant-qrel-docs/labels.txt", "r", "utf-8").readlines())

print('data loaded')

def size_mb(docs):
	return sum(len(s.encode('utf-8')) for s in docs) / 1e6

data_train_size_mb = size_mb(data_train.data)
data_test_size_mb = size_mb(data_test.data)
data_res_size_mb = size_mb(data_res.data)
#data_relevant_qrels_size_mb = size_mb(data_relevant_qrels.data)

print("%d documents - %0.3fMB (training set)" % (
	len(data_train.data), data_train_size_mb))
print("%d documents - %0.3fMB (test set)" % (
	len(data_test.data), data_test_size_mb))
print("%d documents - %0.3fMB (res set)" % (
	len(data_res.data), data_res_size_mb))
#print("%d documents - %0.3fMB (res set)" % (
#	len(data_relevant_qrels.data), data_relevant_qrels_size_mb))
print("%d categories" % len(categories))
print()

# split a training set and a test set
y_train, y_test = data_train.target, data_test.target

print("Extracting features from the training data using a sparse vectorizer")
t0 = time()
if opts.use_hashing:
	vectorizer = HashingVectorizer(stop_words='english', non_negative=True,
								   n_features=opts.n_features)
	X_train = vectorizer.transform(data_train.data)
else:
	vectorizer = TfidfVectorizer(sublinear_tf=True, max_df=0.5,
								 stop_words='english')
	X_train = vectorizer.fit_transform(data_train.data)
duration = time() - t0
print("done in %fs at %0.3fMB/s" % (duration, data_train_size_mb / duration))
print("n_samples: %d, n_features: %d" % X_train.shape)
print()

print("Extracting features from the test data using the same vectorizer")
t0 = time()
X_test = vectorizer.transform(data_test.data)
duration = time() - t0
print("done in %fs at %0.3fMB/s" % (duration, data_test_size_mb / duration))
print("n_samples: %d, n_features: %d" % X_test.shape)
print()

print("Extracting features from the res data using the same vectorizer")
t0 = time()
X_res = vectorizer.transform(data_res.data)
duration = time() - t0
print("done in %fs at %0.3fMB/s" % (duration, data_res_size_mb / duration))
print("n_samples: %d, n_features: %d" % X_res.shape)
print()

#print("Extracting features from the relevant qrel docs data using the same vectorizer")
#t0 = time()
#X_relevant_qrel_docs = vectorizer.transform(data_relevant_qrels.data)
#duration = time() - t0
#print("done in %fs at %0.3fMB/s" % (duration, data_relevant_qrels_size_mb / duration))
#print("n_samples: %d, n_features: %d" % X_relevant_qrel_docs.shape)
#print()

# mapping from integer feature name to original token string
if opts.use_hashing:
	feature_names = None
else:
	feature_names = vectorizer.get_feature_names()

if opts.select_chi2:
	print("Extracting %d best features by a chi-squared test" %
		  opts.select_chi2)
	t0 = time()
	ch2 = SelectKBest(chi2, k=opts.select_chi2)
	X_train = ch2.fit_transform(X_train, y_train)
	X_test = ch2.transform(X_test)
	if feature_names:
		# keep selected feature names
		feature_names = [feature_names[i] for i
						 in ch2.get_support(indices=True)]
	print("done in %fs" % (time() - t0))
	print()

if feature_names:
	feature_names = np.asarray(feature_names)


def trim(s):
	"""Trim string to fit on terminal (assuming 80-column display)"""
	return s# if len(s) <= 80 else s[:77] + "..."


def getName(clf):
	strClf = str(clf)
	name = strClf.split("(")[0]
 	loss = re.search("loss='(\w+)'", strClf)
 	penalty = re.search("penalty='(\w+)'", strClf)
 	alpha = re.search("alpha=([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)", strClf)
 	if loss:
 		name += "." + loss.group(1)
 	if penalty:
 		name += "." + penalty.group(1)
# 	if alpha:
# 		name += "." + alpha.group(1)
	return name

###############################################################################
# Benchmark classifiers
def benchmark(clf):
	print('_' * 80)
	print("Training: " + getName(clf))
	print(clf)
	t0 = time()
	clf.fit(X_train, y_train)
	train_time = time() - t0
	print("train time: %0.3fs" % train_time)

	t0 = time()
	pred = clf.predict(X_test)
	test_time = time() - t0
	print("test time:  %0.3fs" % test_time)
	
	f = open(os.path.join(results_dir, "results.txt." + getName(clf)), "w")
	for p in clf.predict(X_res):
		f.write("%f\n" % p)
	f.close()

	score = metrics.accuracy_score(y_test, pred)
	print("accuracy classifier: %0.3f\t" % (score))
#	score_qrels = metrics.accuracy_score(data_relevant_qrels.target, clf.predict(X_relevant_qrel_docs))
#	print("accuracy classifier: %0.3f\t qrels: %0.3f" % (score, score_qrels))

	
	if hasattr(clf, 'coef_'):
		print("dimensionality: %d %d" % (clf.coef_.shape[0], clf.coef_.shape[1]))
		print("density: %f" % density(clf.coef_))

		if opts.print_top10 and feature_names is not None:
			print("top 10 keywords per class:")
			for i, category in enumerate(categories):
				top10 = np.argsort(clf.coef_[0])[-10:]
				print(trim("%s: %s"
					  % (category, " ".join(feature_names[top10]))))
		print()

	if opts.print_report:
		print("classification report:")
		print(metrics.classification_report(y_test, pred,
											target_names=categories))

	if opts.print_cm:
		print("confusion matrix:")
		print(metrics.confusion_matrix(y_test, pred))

	print()
	clf_descr = str(clf).split('(')[0]
	return clf_descr, score, train_time, test_time


results = []

# LinearSVC
results.append(benchmark(LinearSVC(loss="squared_hinge", penalty="l2", dual=False, tol=1e-3)))

# SGDClassifier
for loss in ["hinge", "squared_loss",  "epsilon_insensitive"]:
	for penalty in ["l2", "elasticnet"]:
		results.append(benchmark(SGDClassifier(loss=loss, alpha=.0001, n_iter=500, penalty=penalty, n_jobs=-1)))

#results.append(benchmark(SGDClassifier(loss="hinge", alpha=.0001, n_iter=500, penalty="l2", n_jobs=-1)))

#print('=' * 80)
#print("LinearSVC with L1-based feature selection")
## The smaller C, the stronger the regularization.
## The more regularization, the more sparsity.
#results.append(benchmark(Pipeline([
#  ('feature_selection', LinearSVC(penalty="l1", dual=False, tol=1e-3)),
#  ('classification', LinearSVC())
#])))

results.append(benchmark(Pipeline([
	('feature_selection', SelectFromModel(SGDClassifier(loss="epsilon_insensitive", n_iter=500, penalty="l2", n_jobs=-1))),
	('classification', SGDClassifier(loss="epsilon_insensitive", n_iter=500, penalty="l2", n_jobs=-1))
])))
