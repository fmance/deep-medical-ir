#!/bin/bash

rsync -vP data/$1/train/labels-nn-hedges.txt mancef@ela.cscs.ch:/home/mancef/labels-nn.txt
rsync -vP data/$1/train/mappings-hedges.txt mancef@ela.cscs.ch:/home/mancef/mappings.txt
