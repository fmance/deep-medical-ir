#!/bin/python

import os, codecs
from shutil import copyfile
import random

MAX_DOC_LEN = 1000

class_id = "treat"
class_dir = "../data/nn/" + class_id + "/"
output_class_dir = "res/" + class_id + "/"

train_doc_ids = map(lambda did: int(did), open(class_dir + "train/ids.txt").read().split())
num_train_pos = len(train_doc_ids) / 2
train_labels = [1] * num_train_pos + [0] * num_train_pos

test_doc_ids = map(lambda did: int(did), open(class_dir + "test/ids.txt").read().split())
num_test_pos = len(test_doc_ids) / 2
test_labels = [1] * num_test_pos + [0] * num_test_pos

res_doc_ids = map(lambda did: int(did), open(class_dir + "res/ids.txt").read().split())

all_docs = set(train_doc_ids) | set(test_doc_ids)

def write_labels(labels, filename):
    print "Writing labels to " + filename
    f = open(filename, "w")
    for label in labels:
        f.write("%d\n" % label)
    f.close()

def write_doc_mapping(doc_ids, filename):
    print "Writing doc mappings to " + filename

    f = codecs.open(filename, "w", "utf-8")

    for doc_id in doc_ids:
        words = codecs.open(os.path.join(class_dir + "labeled/", str(doc_id) + ".txt.sent"), "r", "utf-8").read().split()
        for w in words:
            f.write("%s " % w)
        f.write("\n")

    f.close()

def write_doc_ids(doc_ids, filename):
    f = open(filename, "w")
    for doc_id in doc_ids:
        f.write("%d\n" % doc_id)
    f.close()

def write_datasets():
    print "Writing training set"
    write_labels(train_labels,  output_class_dir + "train/labels.txt")
    write_doc_mapping(train_doc_ids, output_class_dir + "train/docs.txt")
    write_doc_ids(train_doc_ids, output_class_dir + "train/ids.txt")

    print "Writing test set"
    write_labels(test_labels, output_class_dir + "test/labels.txt")
    write_doc_mapping(test_doc_ids, output_class_dir + "test/docs.txt")
    write_doc_ids(test_doc_ids, output_class_dir + "test/ids.txt")

    print "Writing res set"
    write_doc_mapping(res_doc_ids, output_class_dir + "res/docs.txt")
    write_doc_ids(res_doc_ids, output_class_dir + "res/ids.txt")

write_datasets()
