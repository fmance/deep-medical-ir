package ch.ethz.inf.da.cds.ir;

public class Article {
	private final String pmcid;
	private final String abstr;
	private final String title;
	private final String text;

	public Article(String pmcid, String title, String abstr, String text) {
		this.pmcid = pmcid;
		this.title = title;
		this.abstr = abstr;
		this.text = text;
	}

	public String getPmcid() {
		return pmcid;
	}

	public String getTitle() {
		return title;
	}

	public String getAbstract() {
		return abstr;
	}

	public String getText() {
		return text;
	}

	@Override
	public String toString() {
		return "Article [pmcid=" + pmcid + "\n title=" + title + "\n abstract=" + abstr + "\n text=" + text + "]";
	}

}
