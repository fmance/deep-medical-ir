import numpy as np
import tensorflow as tf
import os
import time
import sys
from itertools import izip

NUM_CLASSES = 2
VOCAB_SIZE = 4905671 + 1
EMBED_SIZE = 100
MAX_DOC_LEN = 5000 # !!! #

MAX_ITER = 5000
NUM_FILTERS = 100
FC1_SIZE = 50
LEARNING_RATE = 0.001
BATCH_SIZE = 100

DESCRIPTOR = ".".join(map(str, [MAX_ITER, NUM_FILTERS, FC1_SIZE, LEARNING_RATE, BATCH_SIZE]))

def getDescriptor(iterNum):
	return ".".join(map(str, [iterNum, NUM_FILTERS, FC1_SIZE, LEARNING_RATE, BATCH_SIZE]))

category = sys.argv[1]
dataDir = "../data/"
catDir = os.path.join(dataDir, category)
irResDir = os.path.join(dataDir, "res-and-qrels")
resDir = os.path.join(irResDir, "results", category)
resFileRoot = os.path.join(resDir, "results.txt.NN")
testFile = os.path.join(resDir, "results-on-test-docs.txt.NN")

def chunks(l, n):
	n = max(1, n)
	return [l[i:i + n] for i in range(0, len(l), n)]

def read_embeddings():
	return np.reshape(np.fromfile("embeddings.txt", dtype=np.float32, count=-1,sep=" "), (VOCAB_SIZE, EMBED_SIZE))

print DESCRIPTOR, "reading embeddings"
sys.stdout.flush()
embeddings = tf.constant(read_embeddings())
#embeddings = tf.Variable(tf.random_uniform([VOCAB_SIZE, EMBED_SIZE], -1.0, 1.0), name="embeddings")
print DESCRIPTOR, "done"
sys.stdout.flush()

def readDocsAndLabels(dirname):
	print DESCRIPTOR, "Reading docs and labels from " + dirname
	sys.stdout.flush()

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

#numTrainDocs = len(trainDocs)
#BATCH_SIZE = 100
#batchChunks = chunks(np.random.permutation(np.arange(numTrainDocs)), BATCH_SIZE)
#batchChunkIterator = 0

#def getTrainingBatch():
#	global batchChunks, batchChunkIterator

#	if batchChunkIterator >= len(batchChunks):
#		print "\n\nend of batches, chunkIterator = %d\n\n" % batchChunkIterator
#		sys.stdout.flush()
#		batchChunks = chunks(np.random.permutation(np.arange(numTrainDocs)), BATCH_SIZE)
#		batchChunkIterator = 0

#	print "getting batch %d" % batchChunkIterator
#	sys.stdout.flush()
#	currentChunk = batchChunks[batchChunkIterator]
#	batchChunkIterator += 1
#	
#	return trainDocs[currentChunk], trainLabels[currentChunk]
	

# each row is an array corresponding to indices of the words in the vocabulary
x = tf.placeholder(tf.int32, [None, MAX_DOC_LEN], name = "x")

# each row is a one-hot vector for the class of that document
y_ = tf.placeholder(tf.float32, shape=[None, NUM_CLASSES], name = "y_")

keep_prob = tf.placeholder(tf.float32, name = "keep_prob")

l2_loss_fc1 = tf.constant(0.0)
l2_loss_conv1 = tf.constant(0.0)

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
	l2_loss_conv1 += tf.nn.l2_loss(W_conv1)
	l2_loss_conv1 += tf.nn.l2_loss(b_conv1)

NUM_FILTERS_TOTAL = NUM_FILTERS * len(filter_sizes)
h_pool = tf.reshape(tf.concat(3, poolings), [-1, NUM_FILTERS_TOTAL], name="h_pool")
h_drop = tf.nn.dropout(h_pool, keep_prob, name="h_drop")

# Without second FC layer
#W_fc1 = tf.get_variable("W_fc1", shape=[NUM_FILTERS_TOTAL, NUM_CLASSES], initializer=tf.contrib.layers.xavier_initializer())
#b_fc1 = bias_variable([NUM_CLASSES], "b_fc1")

#l2_loss_fc1 += tf.nn.l2_loss(W_fc1)
#l2_loss_fc1 += tf.nn.l2_loss(b_fc1)

#scores = tf.nn.xw_plus_b(h_drop, W_fc1, b_fc1, name="scores")
# End W/O second FC layer

# With second FC layer
W_fc1 = weight_variable([NUM_FILTERS_TOTAL, FC1_SIZE], "W_fc1")
b_fc1 = bias_variable([FC1_SIZE], "b_fc1")
h_fc1 = tf.nn.bias_add(tf.matmul(h_drop, W_fc1), b_fc1, name="h_fc1")

W_fc2 = weight_variable([FC1_SIZE, NUM_CLASSES], "W_fc2")
b_fc2 = bias_variable([NUM_CLASSES], "b_fc2")

scores = tf.nn.bias_add(tf.matmul(h_fc1, W_fc2), b_fc2, name="scores")
# End With second FC layer

predictions =  tf.argmax(scores, 1, name="predictions")

loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(scores, y_)) #+ 1e-5 * l2_loss_conv1 + 1e-4 * l2_loss_fc1

correct_prediction = tf.equal(predictions, tf.argmax(y_,1), name="correct_prediction")
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32), name="accuracy")

#y_conv=tf.nn.softmax(scores)
#cross_entropy = -tf.reduce_sum(y_*tf.log(tf.clip_by_value(y_conv,1e-10,1.0)))

train_step = tf.train.AdamOptimizer(learing_rate=LEARNING_RATE).minimize(loss)

# Add ops to save and restore all the variables.
saver = tf.train.Saver()

sess = tf.InteractiveSession()

############# TODO comment out when restoring
sess.run(tf.initialize_all_variables())
#############

#saver.restore(sess, os.path.join(resDir, "nn5000.save"))

def evaluate(outfile, doc_chunks, label_chunks):
	print DESCRIPTOR, "Evaluating"
	sys.stdout.flush()

	sum_acc = 0.0
	sum_w = 0.0
	pred = open(outfile, "w")
	counter = 0
	for tdc, tlc in zip(doc_chunks, label_chunks):
		scr, prd, test_accuracy = sess.run([scores, predictions, accuracy], feed_dict={
			x: tdc, y_: tlc, keep_prob: 1.0})
		for idx in range(0, len(tdc)):
			scoreIdx = scr[idx]
			pred.write("%f %f\n" % (scoreIdx[0], scoreIdx[1]))
		sum_acc += len(tdc) * test_accuracy
		sum_w += len(tdc)
		counter += 1
		print DESCRIPTOR, "Evaluating chunk %d" % counter
		sys.stdout.flush()

	pred.close()
	acc = sum_acc/sum_w
	print DESCRIPTOR, "\n\ntotal test docs %d: test accuracy %g\n\n" % (sum_w, acc)
	sys.stdout.flush()

	return acc

def train(offset, num_iter):
	acc_train = 0.0
	for it in range(offset, offset+num_iter+1):
		batch = getTrainingBatch(BATCH_SIZE)
		_, train_loss, train_accuracy, train_l2_conv1, train_l2_fc1 = sess.run([train_step, loss, accuracy, l2_loss_conv1, l2_loss_fc1], feed_dict={
			x:batch[0], y_: batch[1], keep_prob: 0.5})
		print(DESCRIPTOR + 
			"step %d, l2 loss conv1 %g, l2 loss fc1 %g, loss %g, training accuracy %g"%(it, train_l2_conv1, train_l2_fc1, train_loss, train_accuracy))
		sys.stdout.flush()

		acc_train += train_accuracy

#		if it > 0 and it % 1000 == 0:
#			acc_test = evaluate(testFile, testDocsChunks, testLabelsChunks)
#			print "accuracy:\t\ttrain: %g\t\ttest: %g" % (acc_train/it, acc_test)
#			sys.stdout.flush()
		if it > 0 and it % 500 == 0:
			iterDescriptor = getDescriptor(it)
			evaluate(resFile + "." + iterDescriptor, resultDocsChunks, resultDummyLabelsChunks)
			print DESCRIPTOR, "Saving checkpoint"
			saver.save(sess, os.path.join(resDir, "nn" + iterDescriptor + ".save"))
			print DESCRIPTOR, "Done checkpoint"

train(0, MAX_ITER)

evaluate(resFile + "." + DESCRIPTOR, resultDocsChunks, resultDummyLabelsChunks)

print DESCRIPTOR, "Saving checkpoint"
sys.stdout.flush()

saver.save(sess, os.path.join(resDir, "nn" + DESCRIPTOR + ".save"))

print DESCRIPTOR, "Done"
