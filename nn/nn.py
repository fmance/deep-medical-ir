#!/usr/bin/python

import tensorflow as tf
import numpy as np
import os
import time

NUM_CLASSES = 3
#VOCAB_SIZE = 4262098
VOCAB_SIZE = 607425
EMBED_SIZE = 100
#FILTER_DIM = 5
NUM_FILTERS = 100
MAX_DOC_LEN = 500

# !!!!!!!!!!!!!!!
NUM_TRAIN_DOCS = 6270
# !!!!!!!!!!!!!!!

def read_embeddings():
    return np.reshape(np.fromfile("../data/training/w2v.txt", dtype=np.float32, count=-1,sep=" "), (VOCAB_SIZE, EMBED_SIZE))

print "reading embeddings"
embeddings = tf.constant(read_embeddings())
#embeddings = tf.Variable(
#                tf.random_uniform([VOCAB_SIZE, EMBED_SIZE], -1.0, 1.0),
#                name="W")
print "done"

print "reading labels"
labels = np.reshape(np.fromfile("../data/training/labels.txt", dtype=np.int32, count=-1,sep=" "), (NUM_TRAIN_DOCS, 3))
#labels = tf.Variable(tf.random_uniform([NUM_TRAIN_DOCS, 3], -1,1))
print "done"

print "reading training docs"
docs = np.reshape(np.fromfile("../data/training/docs.txt", dtype=np.int32, count=-1,sep=" "), (NUM_TRAIN_DOCS, MAX_DOC_LEN))
#docs = tf.Variable(tf.random_uniform([NUM_TRAIN_DOCS, MAX_DOC_LEN], -1,1))
print "done"

def get_batch(size):
    shuffle_indices = np.random.permutation(np.arange(NUM_TRAIN_DOCS))
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

def weight_variable(shp):
  return tf.Variable(tf.truncated_normal(shp, stddev=0.1))

def bias_variable(shp):
  return tf.Variable(tf.constant(0.1, shape=shp))

def conv2d(x, W):
  return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='VALID')

def max_pool(x, filter_size):
  return tf.nn.max_pool(x, ksize=[1, MAX_DOC_LEN - filter_size + 1, 1, 1],
                        strides=[1, 1, 1, 1], padding='VALID')

filter_sizes = [5]

#convolution filter

poolings = []

for filter_size in filter_sizes:
    W_conv1 = weight_variable([filter_size, EMBED_SIZE, 1, NUM_FILTERS])
    b_conv1 = bias_variable([NUM_FILTERS])
    h_conv1 = tf.nn.relu(tf.nn.bias_add(conv2d(embed_expanded, W_conv1), b_conv1))
    h_pool1 = max_pool(h_conv1, filter_size)
    poolings.append(h_pool1)
    
NUM_FILTERS_TOTAL = NUM_FILTERS * len(filter_sizes)
h_pool = tf.reshape(tf.concat(3, poolings), [-1, NUM_FILTERS_TOTAL])
h_drop = tf.nn.dropout(h_pool, keep_prob)

W_fc1 = weight_variable([NUM_FILTERS_TOTAL, NUM_CLASSES])
b_fc1 = bias_variable([NUM_CLASSES])

scores = tf.nn.bias_add(tf.matmul(h_drop, W_fc1), b_fc1)
predictions =  tf.argmax(scores, 1)

loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(scores, y_))

correct_prediction = tf.equal(predictions, tf.argmax(y_,1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))


#y_conv=tf.nn.softmax(scores)
#cross_entropy = -tf.reduce_sum(y_*tf.log(tf.clip_by_value(y_conv,1e-10,1.0)))

train_step = tf.train.AdamOptimizer(1e-4).minimize(loss)

sess = tf.InteractiveSession()
sess.run(tf.initialize_all_variables())
for it in range(20000):
    print "getting batch"
    batch = get_batch(100)
    print "done"
    #  if i%10 == 0:
    #      train_accuracy = accuracy.eval(feed_dict={
    #            x:batch[0], y_: batch[1], keep_prob: 1.0})
    _, train_loss, train_accuracy = sess.run([train_step, loss, accuracy], feed_dict={
        x:batch[0], y_: batch[1], keep_prob: 0.5})
    print("step %d, loss %g, training accuracy %g"%(it, train_loss, train_accuracy))
    #  train_step.run(feed_dict={x: batch[0], y_: batch[1], keep_prob: 0.5})

print "reading test labels"
test_labels = np.reshape(np.fromfile("../data/test/labels.txt", dtype=np.int32, count=-1,sep=" "), (-1, 3))
print "done"

print "reading test docs"
test_docs = np.reshape(np.fromfile("../data/test/docs.txt", dtype=np.int32, count=-1,sep=" "), (-1, MAX_DOC_LEN))
print "done"

print "predictions\n\n"

for b in range(45):
    print "\n\ngetting test batch " + str(b)
    cur = 100*b
    docs_test_b = test_docs[cur:cur+100]
    labels_test_b = test_labels[cur:cur+100]
    pr = scores.eval(feed_dict={
        x: docs_test_b, y_: labels_test_b, keep_prob: 1.0})
    for i in range(0, 100):
        pri = pr[i]
        lab = test_labels[i]
        print "%.10f   %.10f   %.10f ---> %d %d %d" % (pri[0], pri[1], pri[2], lab[0], lab[1], lab[2])

    print("test accuracy %g"%accuracy.eval(feed_dict={
        x: docs_test_b, y_: labels_test_b, keep_prob: 1.0}))
