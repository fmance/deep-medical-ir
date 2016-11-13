DIVISION_CUTOFFS = {"SVMPerf" : 4.0,
					"SGDClassifier": 4.0, # 8 ok
					"LinearSVC" : 4.0, # 4,6,8 also ok
					"LogisticRegression" : 4.0,
					"NN": 4.0,
					"PassiveAggressiveClassifier": 4.0,
					"Perceptron": 4.0,
					"RidgeClassifier": 4.0,
					"Pipeline": 4.0,
					"MultinomialNB": 4.0,
					"MLPClassifier": 4.0}
					
MAX_CUTOFFS = {"SVMPerf" : 1.0,
			   "SGDClassifier":1.0,
			   "LinearSVC" : 1.0,
			   "NN": 1.0,
			   "RidgeClassifier": 1.0}
			   
BASIC_WEIGHTS = {"SVMPerf": 0.5,
				 "SGDClassifier": 0.5,
				 "LinearSVC" : 0.5,
				 "LogisticRegression" : 0.5,
				 "NN": 0.5,
				 "PassiveAggressiveClassifier": 0.5,
				 "Perceptron": 0.5,
				 "RidgeClassifier": 0.5,
				 "Pipeline": 0.5,
				 "MultinomialNB": 0.5,
				 "MLPClassifier": 0.5}

def getBm25Weight(classId, target):
	if "sum" in target:
		if classId == "diag":
			return 0.75
		if classId == "test":
			return 0.85
		if classId == "treat":
			return 0.8
	if "desc" in target or "note" in target:
		if classId == "diag":
			return 0.75
		if classId == "test":
			return 0.85
		if classId == "treat":
			return 0.8

def getClassifierWeight(classId, target):
	if "sum" in target:
		if classId == "diag":
			return 0.5
		if classId == "test":
			return 0.1
		if classId == "treat":
			return 0.5
	if "desc" in target or "note" in target:
		if classId == "diag":
			return 0.5
		if classId == "test":
			return 0.1
		if classId == "treat":
			return 0.5

def getTopicModelWeight(classId, target):
	if "sum" in target:
		if classId == "diag":
			return 0.95
		if classId == "test":
			return 0.9
		if classId == "treat":
			return 0.95
	if "desc" in target or "note" in target:
		if classId == "diag":
			return 0.9
		if classId == "test":
			return 0.85
		if classId == "treat":
			return 0.85
			

