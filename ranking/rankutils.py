import os
import sys
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from collections import defaultdict
import numpy as np
import math

def printBestWeights(bestWeights):
	bestWeightsDict = defaultdict(list)
	for w, cw in bestWeights:
		bestWeightsDict[w].append(cw)
	for w in sorted(bestWeightsDict.keys()):
		print "%f: " % w,
		for cw in bestWeightsDict[w]:
			print "%f " % cw,
		print
		
def plotAllp10s3d(allP10s):
	bm25Weights, classifierWeights, p10s = zip(*allP10s)
	p10Base = p10s[-1]
	
	BM25_WEIGHTS = sorted(list(set(bm25Weights)))
	CLASSIFIER_WEIGHTS = sorted(list(set(classifierWeights)))
	
#	p10s = [p10 if p10 > p10Base else np.nan for p10 in p10s]
	
	X = [[w] * len(CLASSIFIER_WEIGHTS) for w in BM25_WEIGHTS]
	Y = CLASSIFIER_WEIGHTS # [CLASSIFIER_WEIGHTS * len(BM25_WEIGHTS)]
	Z = np.split(np.array(p10s), len(BM25_WEIGHTS))

#	Z_BASE = [[p10Base] * len(CLASSIFIER_WEIGHTS)] * len(BM25_WEIGHTS)

	fig = plt.figure()
	ax=Axes3D(fig)
	ax.set_xlabel("BM25 Weights")
	ax.set_ylabel("CLASSIFIER Weights")
	ax.set_zlabel("Score")
	
	ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.terrain, vmin=p10Base)
#	ax.plot_surface(X, Y, Z_BASE, color="r")
	plt.show()
	
def plotAllp10sContour(allP10s, title, saveDir):
	bm25Weights, classifierWeights, p10s, p10Vars = zip(*allP10s)
	p10Base = p10s[-1]

	p10Dict = {}
	varDict = {}	
	for bw, cw, p10, varP10 in allP10s:
		p10Dict[(bw, cw)] = p10 - p10Base #if score > p10Base else 0.0
		varDict[(bw, cw)] = varP10

	X = sorted(list(set(bm25Weights)))
	Y = sorted(list(set(classifierWeights)))
	Z = [[p10Dict[(x,y)] for x in X] for y in Y]
	ZVar = [[varDict[(x,y)] for x in X] for y in Y]
	levels=np.hstack([np.array([-0.3]), np.arange(-0.15,-0.0001,0.01), np.array([-0.0001,0.0001]), np.arange(0.01,0.16,0.01), np.array([0.3])])
	#  range(-20,0,1)+[-0.000001,0.000001]+range(1,21,1) #np.arange(-0.18, 0.19, 0.015)

	plt.subplot(211)
	cs = plt.contourf(X,Y,Z, levels=levels, cmap=cm.seismic)
#	cs = plt.contourf(X,Y,Z, vmax=0, levels=np.arange(-0.16,0.02,0.02), cmap=cm.Greys)
	plt.colorbar(ticks=levels, format="%.4f")
	plt.xticks(np.arange(0.0, 1.0, 0.1))
	plt.yticks(np.arange(0.0, 1.0, 0.1))
	plt.grid(linewidth=2)

#	plt.contour(cs, colors='k')
#	cs = plt.contour(X,Y,Z, vmin=p10Base, levels=levels, cmap=cm.Oranges)
#	plt.clabel(cs, inline=True, fmt='%.2f', colors='k', fontsize=10)
	
	plt.title(title + " - P10 MEAN")
	plt.xlabel("BM25 Weight")
	plt.ylabel("CLASSIFIER Weight")
	
	plt.subplot(212)
	levelsVar = np.arange(0, 0.08, 0.001)
	cs = plt.contourf(X,Y,ZVar, levels=levelsVar, cmap=cm.PuBu)
	plt.colorbar(ticks=np.arange(0, 0.08, 0.01))
	plt.xticks(np.arange(0.0, 1.0, 0.1))
	plt.yticks(np.arange(0.0, 1.0, 0.1))
	plt.grid(linewidth=2)
	plt.title(title + " - P10 VARIANCE")
	plt.xlabel("BM25 Weight")
	plt.ylabel("CLASSIFIER Weight")
	
	
	matplotlib.rcParams.update({'font.size': 20})

	fig = matplotlib.pyplot.gcf()
	fig.set_size_inches(25, 25)

	plt.savefig(saveDir + "/" + title.replace(" ", "").replace(",", "-") + ".png")
#	plt.show()

