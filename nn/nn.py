#!/usr/bin/python

import tensorflow as tf
import numpy as np
import os
import time
from itertools import izip

NUM_CLASSES = 2
VOCAB_SIZE = 1726928
EMBED_SIZE = 100
NUM_FILTERS = 50
MAX_DOC_LEN = 1000

FC1_SIZE = 25

class_id = "treat"
class_dir = "../data/nn/" + class_id + "/"
class_res_dir = "res/" + class_id + "/"

def chunks(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]

def read_embeddings():
    return np.reshape(np.fromfile("embeddings.txt", dtype=np.float32, count=-1,sep=" "), (VOCAB_SIZE, EMBED_SIZE))

print "reading embeddings"
embeddings = tf.constant(read_embeddings())
#embeddings = tf.Variable(
#                tf.random_uniform([VOCAB_SIZE, EMBED_SIZE], -1.0, 1.0),
#                name="embeddings")
print "done"

#print "reading labels"
#labels = np.reshape(np.fromfile(class_dir + "train/labels.txt", dtype=np.int32, count=-1,sep=" "), (-1, NUM_CLASSES))
#print "done"

#print "reading training docs"
#docs = np.reshape(np.fromfile(class_dir + "train/docs.txt", dtype=np.int32, count=-1,sep=" "), (-1, MAX_DOC_LEN))
#print "done"

#print "reading test labels"
#test_labels_pos = np.reshape(np.fromfile(class_dir + "test/pos-labels.txt", dtype=np.int32, count=-1,sep=" "), (-1, NUM_CLASSES))
#print "done"

#print "reading test docs"
#test_docs_pos = np.reshape(np.fromfile(class_dir + "test/pos-docs.txt", dtype=np.int32, count=-1,sep=" "), (-1, MAX_DOC_LEN))
#print "done"

#print "reading test labels"
#test_labels_neg = np.reshape(np.fromfile(class_dir + "test/neg-labels.txt", dtype=np.int32, count=-1,sep=" "), (-1, NUM_CLASSES))
#print "done"

#print "reading test docs"
#test_docs_neg = np.reshape(np.fromfile(class_dir + "test/neg-docs.txt", dtype=np.int32, count=-1,sep=" "), (-1, MAX_DOC_LEN))
#print "done"

print "reading result docs"
res_docs = np.reshape(np.fromfile(class_dir + "res/docs.txt", dtype=np.int32, count=-1,sep=" "), (-1, MAX_DOC_LEN))
res_labels_dummy = np.reshape([-1, -1] * len(res_docs), (-1, NUM_CLASSES))
print "done"

print "reading qrel docs"
qrel_docs = np.reshape(np.fromfile(class_dir + "qrels/docs.txt", dtype=np.int32, count=-1,sep=" "), (-1, MAX_DOC_LEN))
qrel_labels_dummy = np.reshape([-1, -1] * len(qrel_docs), (-1, NUM_CLASSES))
print "done"

#test_doc_pos_chunks = chunks(test_docs_pos, 100)
#test_label_pos_chunks = chunks(test_labels_pos, 100)

#test_doc_neg_chunks = chunks(test_docs_neg, 100)
#test_label_neg_chunks = chunks(test_labels_neg, 100)

res_docs_chunks = chunks(res_docs, 100)
res_labels_dummy_chunks = chunks(res_labels_dummy, 100)

qrel_docs_chunks = chunks(qrel_docs, 100)
qrel_labels_dummy_chunks = chunks(qrel_labels_dummy, 100)

def get_batch(size):
    shuffle_indices = np.random.permutation(np.arange(len(docs)))
    shuffle_indices = shuffle_indices[:size]
    shuffle_docs = docs[shuffle_indices]
    shuffle_labels = labels[shuffle_indices]
    return shuffle_docs, shuffle_labels

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

filter_sizes = [2,3,4,5]

#convolution filter

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

W_fc1 = weight_variable([NUM_FILTERS_TOTAL, FC1_SIZE], "W_fc1")
b_fc1 = bias_variable([FC1_SIZE], "b_fc1")
h_fc1 = tf.nn.bias_add(tf.matmul(h_drop, W_fc1), b_fc1, name="h_fc1")

W_fc2 = weight_variable([FC1_SIZE, NUM_CLASSES], "W_fc2")
b_fc2 = bias_variable([NUM_CLASSES], "b_fc2")

scores = tf.nn.bias_add(tf.matmul(h_fc1, W_fc2), b_fc2, name="scores")
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
#sess.run(tf.initialize_all_variables())
#############

saver.restore(sess, "res/" + class_id + "/nn5000" + class_id + ".save")

def evaluate(filename, doc_chunks, label_chunks):
    sum_acc = 0.0
    sum_w = 0.0
    pred = open(filename, "w")
    for tdc, tlc in zip(doc_chunks, label_chunks):
        scr, prd, test_accuracy = sess.run([scores, predictions, accuracy], feed_dict={
            x: tdc, y_: tlc, keep_prob: 1.0})
        for idx in range(0, len(tdc)):
            pred.write("%g %f %f\n" % (prd[idx], scr[idx][0], scr[idx][1]))
        sum_acc += len(tdc) * test_accuracy
        sum_w += len(tdc)
    pred.close()
    acc = sum_acc/sum_w
    print "\n\ntotal test docs %d: test accuracy %g\n\n" % (sum_w, acc)
    return acc

def train(offset, num_iter):
    acc_train = 0.0
    for it in range(offset, offset+num_iter):
        batch = get_batch(100)
        _, train_loss, train_accuracy = sess.run([train_step, loss, accuracy], feed_dict={
            x:batch[0], y_: batch[1], keep_prob: 0.5})
        print("step %d, loss %g, training accuracy %g"%(it, train_loss, train_accuracy))
        acc_train += train_accuracy
        
        if it > 0 and it % 1000 == 0:
            acc_pos = evaluate(class_res_dir + "test-pos-predictions.txt", test_doc_pos_chunks, test_label_pos_chunks)
            acc_neg = evaluate(class_res_dir + "test-neg-predictions.txt", test_doc_neg_chunks, test_label_neg_chunks)
            ovr = (acc_pos + acc_neg) / 2
            print "overall accuracy:\t\ttrain: %g\t\ttest: %g" % (acc_train/it, ovr)
            evaluate(class_res_dir + "predictions-on-ir-res.txt", res_docs_chunks, res_labels_dummy_chunks)
            evaluate(class_res_dir + "predictions-on-qrels.txt", qrel_docs_chunks, qrel_labels_dummy_chunks)
        if it > 0 and it % 1000 == 0:
            saver.save(sess, class_res_dir + "nn" + str(it) + class_id + ".save")

#train(5001, 10000)
evaluate(class_res_dir + "predictions-on-ir-res.txt", res_docs_chunks, res_labels_dummy_chunks)
evaluate(class_res_dir + "predictions-on-qrels.txt", qrel_docs_chunks, qrel_labels_dummy_chunks)
