package ch.ethz.inf.da.cds.ir;

public class Article {
	private final String pmcid;
	private final String title;
	private final String text;

	public Article(String pmcid, String title, String text) {
		this.pmcid = pmcid;
		this.title = title;
		this.text = text;
	}

	public String getPmcid() {
		return pmcid;
	}

	public String getTitle() {
		return title;
	}

	public String getText() {
		return text;
	}

	@Override
	public String toString() {
		return "Article [pmcid=" + pmcid + "\n title=" + title + "\n text=" + text + "]";
	}

}
