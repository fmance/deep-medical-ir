import matplotlib.pyplot as plt
import matplotlib

labels = ["Linear\nRegression", "AdaRank", "RankNet", "Coord\nAscent", "LambdaMART", "MART", "RankBoost"]
X=[0.5 + x for x in range(0,len(labels))]
perf = [5.08, 4.92, 4.00, 3.75, 2.09, 0.75, 0.25]
unjudged = [6.25, 6, 8.25, 7.25, 11.25, 11.75, 13]

plt.style.use("ggplot")

fig, ax1 = plt.subplots()

ax1.plot(X, perf, "-o", color="#BD2828", linewidth=2)
for i, p in enumerate(perf):
	xpos = X[i]
	ypos = p+0.1
	if i == 6:
		xpos -= 0.2
	ax1.annotate("%+.2f%%" % p, (xpos, ypos), fontsize=18, color="#BD2828")

plt.text(0.4, 4.3, "Average P@10\nimprovement", fontsize=20, color="#BD2828")
plt.text(0.5, 1.3, "Percent unjudged\ndocs in Top 10", fontsize=20, color="#1459A8")

ax2 = ax1.twinx()

ax2.plot(X, unjudged, "-o", color="#1459A8", linewidth=2)
for i, unj in enumerate(unjudged):
	xpos = X[i]-0.2
	ypos = unj - 0.4
	if i == 2 or i == 4:
		ypos += 0.6
	if i == 6:
		ypos -= 0.1
	ax2.annotate("%.2f%%" % unj, (xpos, ypos), fontsize=18, color="#1459A8")

plt.xticks(X, labels)

ax1.yaxis.set_visible(False)
ax2.yaxis.set_visible(False)

ax1.spines["top"].set_visible(False)    
ax1.spines["bottom"].set_visible(False)    
ax1.spines["right"].set_visible(False)    
ax1.spines["left"].set_visible(False) 

ax1.get_xaxis().tick_bottom()    
ax1.get_yaxis().tick_left() 

ax1.xaxis.grid(False)
ax1.yaxis.grid(False)
ax2.xaxis.grid(False)
ax2.yaxis.grid(False)

#plt.axis("tight")

ax2.set_ylim((5,14))

plt.title("Average improvements and unjudged documents in Top 10")

matplotlib.rcParams.update({'font.size': 20})
fig = matplotlib.pyplot.gcf()
fig.set_size_inches(15, 10)

plt.savefig("../plots/unjudged.png", bbox_inches="tight", pad_inches=0)
