#!/bin/bash

ranker=$1
train=$2
test=$3

for iter in 5 10 20 30 40 50 60 70 80 90 100 150 200 300 500
do ./train.sh $ranker $train -round $iter -i $iter -epoch $iter -bag $iter ${@:4} && ./score.sh 1 $test
done
