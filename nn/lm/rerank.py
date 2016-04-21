#!/bin/python

import numpy as np

import logging

from rankpy.queries import Queries
from rankpy.queries import find_constant_features

from rankpy.models import LambdaMART

logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.INFO)

#QRELS_2014_FEATURES = "qrels-2014-features.txt"
QRELS_2015_FEATURES = "qrels-2015-features.txt"

#RESULTS_2014_FEATURES = "results-2014-features.txt"
RESULTS_2015_FEATURES = "results-2015-features.txt"

RANKINGS_FILE = "rankings.txt"

training_queries = Queries.load_from_text(QRELS_2015_FEATURES)
validation_queries = Queries.load_from_text(QRELS_2015_FEATURES)
test_queries = Queries.load_from_text(RESULTS_2015_FEATURES)

# Print basic info about query datasets.
logging.info('Train queries: %s' % training_queries)
logging.info('Validation queries: %s' % validation_queries)
logging.info('Test queries: %s' %test_queries)    

logging.info('================================================================================')

# Set this to True in order to remove queries containing all documents
# of the same relevance score -- these are useless for LambdaMART.
remove_useless_queries = False

# Find constant query-document features.
cfs = find_constant_features([training_queries, validation_queries, test_queries])

# Get rid of constant features and (possibly) remove useless queries.
training_queries.adjust(remove_features=cfs, purge=remove_useless_queries)
validation_queries.adjust(remove_features=cfs, purge=remove_useless_queries)
test_queries.adjust(remove_features=cfs)

# Print basic info about query datasets.
logging.info('Train queries: %s' % training_queries)
logging.info('Validation queries: %s' % validation_queries)
logging.info('Test queries: %s' % test_queries)

logging.info('================================================================================')

model = LambdaMART(metric='nDCG', max_leaf_nodes=7, shrinkage=0.1,
                   estopping=5,  n_jobs=-1, min_samples_leaf=10)
model.fit(training_queries, validation_queries=training_queries)

logging.info('================================================================================')

rankings = model.predict_rankings(test_queries)
#print rankings
print model.predict(test_queries, compact=False)

logging.info('%s on the test queries: %.8f'
             % (model.metric, model.evaluate(test_queries, n_jobs=-1)))

out = open(RANKINGS_FILE, "w")
for ranking in rankings:
    out.write(" ".join(map(str, ranking)))
    out.write("\n")
out.close()
