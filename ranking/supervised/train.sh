#!/bin/bash

java -jar trunk/bin/RankLib.jar -train ../../ir/results/features-$2.txt -validate ../../ir/results/features-$2.txt -save model/f1.ca -ranker $1 -metric2t P@10 -metric2T P@10  ${@:3}

#java -jar trunk/bin/RankLib.jar -train ../../ir/results/features-$2.txt -ranker $1 -kcv 5 -kcvmd model/ -kcvmn ca -metric2t P@10 -metric2T P@10  ${@:3}
