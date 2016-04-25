package ch.ethz.inf.da.cds.ir;

public class SearchResult {
	private final String pmcid;
	private final int rank;
	private final float score;

	public SearchResult(String pmcid, int rank, float score) {
		this.pmcid = pmcid;
		this.rank = rank;
		this.score = score;
	}

	public String getPmcid() {
		return pmcid;
	}

	public int getRank() {
		return rank;
	}

	public float getScore() {
		return score;
	}

	@Override
	public String toString() {
		return "SearchResult [pmcid=" + pmcid + ",rank=" + rank + ", score=" + score + "]";
	}

}
