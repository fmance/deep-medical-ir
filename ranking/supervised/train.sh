#!/bin/bash

java -jar trunk/bin/RankLib.jar -train ../../ir/results/features-$2-train.txt -validate ../../ir/results/features-$2-train.txt -feature features.txt -save model/f1.ca -ranker $1 -metric2t P@10 -metric2T P@10  ${@:3}
