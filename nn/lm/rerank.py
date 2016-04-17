#!/bin/python

import numpy as np

import logging

from rankpy.queries import Queries
from rankpy.queries import find_constant_features

from rankpy.models import LambdaMART

logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.INFO)

class_id = "diag"
LM_TRAIN_FILE = "lm-" + class_id + "-train.txt"
LM_TEST_FILE = "lm-" + class_id + "-test.txt"

training_queries = Queries.load_from_text(LM_TRAIN_FILE)
test_queries = Queries.load_from_text(LM_TEST_FILE)

# Print basic info about query datasets.
logging.info('Train queries: %s' % training_queries)
logging.info('Test queries: %s' %test_queries)    

logging.info('================================================================================')

# Set this to True in order to remove queries containing all documents
# of the same relevance score -- these are useless for LambdaMART.
remove_useless_queries = False

# Find constant query-document features.
cfs = find_constant_features([training_queries, test_queries])

# Get rid of constant features and (possibly) remove useless queries.
training_queries.adjust(remove_features=cfs, purge=remove_useless_queries)
test_queries.adjust(remove_features=cfs)

# Print basic info about query datasets.
logging.info('Train queries: %s' % training_queries)
logging.info('Test queries: %s' % test_queries)

logging.info('================================================================================')

model = LambdaMART(metric='nDCG@10', max_leaf_nodes=7, shrinkage=0.1,
                   estopping=5,  n_jobs=-1, min_samples_leaf=50)
model.fit(training_queries, validation_queries=training_queries)

logging.info('================================================================================')

logging.info('%s on the test queries: %.8f'
             % (model.metric, model.evaluate(test_queries, n_jobs=-1)))

model.save('LambdaMART_L7_S0.1_E50_' + model.metric)

rankings = model.predict_rankings(test_queries)
print rankings

out = open("rankings.txt", "w")
for ranking in rankings:
    out.write(" ".join(map(str, ranking)))
    out.write("\n")
out.close()
