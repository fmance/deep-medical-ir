class=$1
c=$2
loss=$3
hedges=$4

trainFile=svmlight/$class.train.svmlight$hedges
testFile=svmlight/$class.res.svmlight$hedges
modelFile=models/$class/SVMPerf.model.$loss.$c$hedges
outputFile=../data/res-and-qrels/results/$class/results.txt.SVMPerf.$loss.$c$hedges

svm_perf_learn -c $c -l $loss -w 3 --p 0.1 $trainFile $modelFile
svm_perf_classify $testFile $modelFile $outputFile
