#!/usr/bin/python

import numpy as np
import tensorflow as tf
import os
import time
import sys
from itertools import izip

NUM_CLASSES = 2
VOCAB_SIZE = 3712634 + 1 #1726928
EMBED_SIZE = 100
NUM_FILTERS = 50
MAX_DOC_LEN = 3000 # !!! #

FC1_SIZE = 25

category = sys.argv[1]
dataDir = "../data/"
catDir = os.path.join(dataDir, category)
irResDir = os.path.join(dataDir, "res-and-qrels")
resDir = os.path.join(irResDir, "results", category)
resFile = os.path.join(resDir, "results.txt.NN")
testFile = os.path.join(resDir, "results-on-test-docs.txt.NN")

def chunks(l, n):
	n = max(1, n)
	return [l[i:i + n] for i in range(0, len(l), n)]

def read_embeddings():
	return np.reshape(np.fromfile("embeddings.txt", dtype=np.float32, count=-1,sep=" "), (VOCAB_SIZE, EMBED_SIZE))

print "reading embeddings"
embeddings = tf.constant(read_embeddings())
#embeddings = tf.Variable(
#				tf.random_uniform([VOCAB_SIZE, EMBED_SIZE], -1.0, 1.0),
#				name="embeddings")
print "done"

def readDocsAndLabels(dirname):
	print "Reading docs and labels from " + dirname
	docs = np.reshape(np.fromfile(os.path.join(dirname, "mappings.txt"), dtype=np.int32, count=-1,sep=" "), (-1, MAX_DOC_LEN))
	labels = np.reshape(np.fromfile(os.path.join(dirname, "labels-nn.txt"), dtype=np.int32, count=-1,sep=" "), (-1, NUM_CLASSES))
	return docs, labels

trainDocs, trainLabels = readDocsAndLabels(os.path.join(catDir, "train"))
testDocs, testLabels = readDocsAndLabels(os.path.join(catDir, "test"))
resultDocs, resultDummyLabels = readDocsAndLabels(irResDir)

testDocsChunks = chunks(testDocs, 100)
testLabelsChunks = chunks(testLabels, 100)

resultDocsChunks = chunks(resultDocs, 100)
resultDummyLabelsChunks = chunks(resultDummyLabels, 100)

def getTrainingBatch(batchSize):
	randomIndices = np.random.permutation(np.arange(len(trainDocs)))[:batchSize]
	return trainDocs[randomIndices], trainLabels[randomIndices]

# each row is an array corresponding to indices of the words in the vocabulary
x = tf.placeholder(tf.int32, [None, MAX_DOC_LEN], name = "x")

# each row is a one-hot vector for the class of that document
y_ = tf.placeholder(tf.float32, shape=[None, NUM_CLASSES], name = "y_")

keep_prob = tf.placeholder(tf.float32, name = "keep_prob")

embed = tf.nn.embedding_lookup(embeddings, x)
embed_expanded = tf.expand_dims(embed, -1)

def weight_variable(shp, n):
	return tf.Variable(tf.truncated_normal(shp, stddev=0.1), name=n)

def bias_variable(shp, n):
	return tf.Variable(tf.constant(0.1, shape=shp), name=n)

def conv2d(x, W):
	return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='VALID')

def max_pool(x, filter_size, n):
	return tf.nn.max_pool(x, ksize=[1, MAX_DOC_LEN - filter_size + 1, 1, 1],
						strides=[1, 1, 1, 1], padding='VALID', name=n)

filter_sizes = [3,4,5]

poolings = []

for filter_size in filter_sizes:
	W_conv1 = weight_variable([filter_size, EMBED_SIZE, 1, NUM_FILTERS], "W_conv1")
	b_conv1 = bias_variable([NUM_FILTERS], "b_conv1")
	h_conv1 = tf.nn.relu(tf.nn.bias_add(conv2d(embed_expanded, W_conv1), b_conv1), name="h_conv1")
	h_pool1 = max_pool(h_conv1, filter_size, "h_pool")
	poolings.append(h_pool1)

NUM_FILTERS_TOTAL = NUM_FILTERS * len(filter_sizes)
h_pool = tf.reshape(tf.concat(3, poolings), [-1, NUM_FILTERS_TOTAL], name="h_pool")
h_drop = tf.nn.dropout(h_pool, keep_prob, name="h_drop")

# Without FC layer
#W_fc1 = weight_variable([NUM_FILTERS_TOTAL, NUM_CLASSES], "W_fc1")
#b_fc1 = bias_variable([NUM_CLASSES], "b_fc1")

#scores = tf.nn.bias_add(tf.matmul(h_drop, W_fc1), b_fc1, name="h_fc1")
# End W/O FC layer

# With FC layer
W_fc1 = weight_variable([NUM_FILTERS_TOTAL, FC1_SIZE], "W_fc1")
b_fc1 = bias_variable([FC1_SIZE], "b_fc1")
h_fc1 = tf.nn.bias_add(tf.matmul(h_drop, W_fc1), b_fc1, name="h_fc1")

W_fc2 = weight_variable([FC1_SIZE, NUM_CLASSES], "W_fc2")
b_fc2 = bias_variable([NUM_CLASSES], "b_fc2")

scores = tf.nn.bias_add(tf.matmul(h_fc1, W_fc2), b_fc2, name="scores")
# End With FC layer

predictions =  tf.argmax(scores, 1, name="predictions")

loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(scores, y_), name="loss")

correct_prediction = tf.equal(predictions, tf.argmax(y_,1), name="correct_prediction")
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32), name="accuracy")

#y_conv=tf.nn.softmax(scores)
#cross_entropy = -tf.reduce_sum(y_*tf.log(tf.clip_by_value(y_conv,1e-10,1.0)))

train_step = tf.train.AdamOptimizer(1e-3).minimize(loss)

# Add ops to save and restore all the variables.
saver = tf.train.Saver()

sess = tf.InteractiveSession()

############# TODO comment out when restoring
sess.run(tf.initialize_all_variables())
#############

#saver.restore(sess, os.path.join(resDir, "nn1000.save"))

def evaluate(outfile, doc_chunks, label_chunks):
	print "Evaluating"
	sum_acc = 0.0
	sum_w = 0.0
	pred = open(outfile, "w")
	counter = 0
	for tdc, tlc in zip(doc_chunks, label_chunks):
		scr, prd, test_accuracy = sess.run([scores, predictions, accuracy], feed_dict={
			x: tdc, y_: tlc, keep_prob: 1.0})
		for idx in range(0, len(tdc)):
			scoreIdx = scr[idx]
			pred.write("%f\n" % (scoreIdx[0] - scoreIdx[1]))
		sum_acc += len(tdc) * test_accuracy
		sum_w += len(tdc)
		counter += 1
		print "Evaluating chunk %d" % counter
	pred.close()
	acc = sum_acc/sum_w
	print "\n\ntotal test docs %d: test accuracy %g\n\n" % (sum_w, acc)
	return acc

def train(offset, num_iter):
	acc_train = 0.0
	for it in range(offset, offset+num_iter):
		batch = getTrainingBatch(100)
		_, train_loss, train_accuracy = sess.run([train_step, loss, accuracy], feed_dict={
			x:batch[0], y_: batch[1], keep_prob: 0.5})
		print("step %d, loss %g, training accuracy %g"%(it, train_loss, train_accuracy))
		acc_train += train_accuracy

		if it > 0 and it % 1000 == 0:
			acc_test = evaluate(testFile, testDocsChunks, testLabelsChunks)
			print "accuracy:\t\ttrain: %g\t\ttest: %g" % (acc_train/it, acc_test)
			#evaluate(resFile, resultDocsChunks, resultDummyLabelsChunks)

train(0, 5001)
print "Saving checkpoint"
saver.save(sess, os.path.join(resDir, "nn5000.save"))
evaluate(resFile, resultDocsChunks, resultDummyLabelsChunks)
