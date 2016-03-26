#!/usr/bin/python

import tensorflow as tf
import numpy as np
import os
import time

NUM_CLASSES = 3
VOCAB_SIZE = 4262098
EMBED_SIZE = 52
FILTER_DIM = 5
NUM_FILTERS = 100
MAX_DOC_LEN = 50000

def read_embeddings():
    return np.reshape(np.fromfile("../data/training/w2v.txt", dtype=np.float32, count=-1,sep=" "), (-1, EMBED_SIZE))

print "reading embeddings"
embeddings = tf.constant(read_embeddings())
print "done"

print "reading labels"
labels = np.reshape(np.fromfile("../data/training/labels.txt", dtype=np.int32, count=-1,sep=" "), (-1, 3))
print "done"

print "reading training docs"
docs = np.reshape(np.fromfile("../data/training/docs.txt", dtype=np.int32, count=-1,sep=" "), (-1, MAX_DOC_LEN))
print "done"

train_size = docs.shape[0]


def get_batch(size):
    shuffle_indices = np.random.permutation(np.arange(train_size))
    shuffle_docs = docs[shuffle_indices]
    shuffle_labels = labels[shuffle_indices]
    return shuffle_docs[0:size], shuffle_labels[0:size]

# each row is an array corresponding to indices of the words in the vocabulary
x = tf.placeholder(tf.int32, [None, MAX_DOC_LEN], name = "x")

# each row is a one-hot vector for the class of that document
y_ = tf.placeholder(tf.float32, shape=[None, NUM_CLASSES], name = "y_")

keep_prob = tf.placeholder(tf.float32, name = "keep_prob")

embed = tf.nn.embedding_lookup(embeddings, x)
embed_expanded = tf.expand_dims(embed, -1)

def weight_variable(shape):
  initial = tf.truncated_normal(shape, stddev=0.1)
  return tf.Variable(initial)

def bias_variable(shape):
  initial = tf.constant(0.1, shape=shape)
  return tf.Variable(initial)

def conv2d(x, W):
  return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='VALID')

def max_pool(x):
  return tf.nn.max_pool(x, ksize=[1, MAX_DOC_LEN - FILTER_DIM + 1, 1, 1],
                        strides=[1, 1, 1, 1], padding='VALID')

#convolution filter
W_conv1 = weight_variable([FILTER_DIM, EMBED_SIZE, 1, NUM_FILTERS])
b_conv1 = bias_variable([NUM_FILTERS])
h_conv1 = tf.nn.relu(tf.nn.bias_add(conv2d(embed_expanded, W_conv1), b_conv1))
h_pool1 = tf.reshape(max_pool(h_conv1), [-1, NUM_FILTERS])
h_drop1 = tf.nn.dropout(h_pool1, keep_prob)

W_fc1 = weight_variable([NUM_FILTERS, NUM_CLASSES])
b_fc1 = bias_variable([NUM_CLASSES])
scores = tf.add(tf.matmul(h_drop1, W_fc1), b_fc1)

y_conv=tf.nn.softmax(scores)
cross_entropy = -tf.reduce_sum(y_*tf.log(tf.clip_by_value(y_conv,1e-10,1.0)))

train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)

sess = tf.InteractiveSession()
correct_prediction = tf.equal(tf.argmax(y_conv,1), tf.argmax(y_,1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
sess.run(tf.initialize_all_variables())
for i in range(100):
  print "getting batch"
  batch = get_batch(100)
  print "done"
  #if i%10 == 0:
  pr = y_conv.eval(feed_dict={
        x:batch[0], y_: batch[1], keep_prob: 1.0})
  for l in pr:
        print "%.10f   %.10f   %.10f" % (l[0], l[1], l[2])
  train_accuracy = accuracy.eval(feed_dict={
        x:batch[0], y_: batch[1], keep_prob: 1.0})
  print("step %d, training accuracy %g"%(i, train_accuracy))
  print "\n\n"
  train_step.run(feed_dict={x: batch[0], y_: batch[1], keep_prob: 0.5})

print "reading test labels"
test_labels = np.reshape(np.fromfile("../data/test/labels.txt", dtype=np.int32, count=-1,sep=" "), (-1, 3))
print "done"

print "reading test docs"
test_docs = np.reshape(np.fromfile("../data/test/docs.txt", dtype=np.int32, count=-1,sep=" "), (-1, MAX_DOC_LEN))
print "done"


print("test accuracy %g"%accuracy.eval(feed_dict={
    x: test_docs, y_: test_labels, keep_prob: 1.0}))
