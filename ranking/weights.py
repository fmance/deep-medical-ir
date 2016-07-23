def getBm25Weight(classId, target):
	if "sum" in target:
		if classId == "diag":
			return 0.5
		if classId == "test":
			return 0.85
		if classId == "treat":
			return 0.5
	if "desc" in target or "note" in target:
		if classId == "diag":
			return 0.5
		if classId == "test":
			return 0.85
		if classId == "treat":
			return 0.5

def getClassifierWeight(classId, target):
	if "sum" in target:
		if classId == "diag":
			return 0.5
		if classId == "test":
			return 0.1
		if classId == "treat":
			return 0.75
	if "desc" in target or "note" in target:
		if classId == "diag":
			return 0.5
		if classId == "test":
			return 0.1
		if classId == "treat":
			return 0.75

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
