#!/usr/bin/python

import gensim
import tensorflow as tf
import numpy as np
import os
import time

QRELS_2014 = "../data/qrels2014.txt"

#VEC_LEN = 100
NUM_CLASSES = 3
#MAX_DOC_LEN = 416007
VOCAB_SIZE = 4262098
EMBED_SIZE = 52

def get_doc_stats():
    max_len = 0
    max_doc = 0
    count_big = 0
    big_docs = []
    big_docs2 = []
    start = time.time()
    count = 0
    vocab = set([])
    for sdir in [os.path.join("../data/sentences", d) for d in ["00", "01", "02", "03"]]:
        for ssdir in [os.path.join(sdir, ssdir) for ssdir in sorted(os.listdir(sdir))]:
            for fname in [os.path.join(ssdir, fname) for fname in sorted(os.listdir(ssdir))]:
                count += 1
                if count % 1000 == 0:
                    print "%d files (%s, %d %s %d %s) in %.2f minutes" % (count, count_big, max_len, max_doc, len(vocab), ssdir, (time.time() - start)/60.0)
                words = open(fname).read().split()
                doc_len = len(words)
                #vocab.update(words)
                if (doc_len > 80000):
                    count_big += 1
                    big_docs.append((os.path.basename(fname), doc_len))
                    big_docs2.append(os.path.basename(fname))
                if (doc_len > max_len):
                    max_len = doc_len
                    max_doc = os.path.basename(fname)
    return max_len, max_doc, len(vocab), count_big, big_docs, big_docs2

print get_doc_stats()

def read_labels(qrels_file):
    count_diag = 0
    count_test = 0
    count_treat = 0
    vectors = np.empty(shape=[0, VEC_LEN])
    labels = np.empty(shape=[0,NUM_CLASSES])
    for line in open(qrels_file):
        qrel = line.split()
        topic = int(qrel[0])
        doc_id = qrel[2]
        relevance = int(qrel[3])
        if topic <= 10:
            if relevance > 0:
                count_diag += 1
                labels = np.vstack([labels, [1,0,0]])
        elif topic <= 20:
            if relevance > 0:
                count_test += 1
                labels = np.vstack([labels, [0,1,0]])
        else:
            if relevance > 0:
                count_treat += 1
                labels = np.vstack([labels, [0,0,1]])
    return labels, count_diag, count_test, count_treat
    

FILTER_DIM = 5
NUM_FILTERS = 100

# each row is an array corresponding to indices of the words in the vocabulary
x = tf.placeholder(tf.int32, [None, MAX_DOC_LEN], name = "x")

# each row is a one-hot vector for the class of that document
y_ = tf.placeholder(tf.float32, shape=[None, NUM_CLASSES], name = "y_")

keep_prob = tf.placeholder(tf.float32, name = "keep_prob")

#TODO use the ones from w2v
embeddings = tf.Variable(tf.random_uniform([VOCAB_SIZE, EMBED_SIZE], -1.0, 1.0))
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
cross_entropy = -tf.reduce_sum(y_*tf.log(y_conv))

tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
